import logging
import time
from urllib.parse import urlencode

import httpx
from django.conf import settings

from common.exceptions.base import ExternalAPIException
from common.logging.context import get_correlation_id

logger = logging.getLogger("driveclear.external")

DEFAULT_HEADERS = {
    "accept": "application/json, text/plain, */*",
    "content-type": "application/json",
    "origin": "https://www.challanpay.in",
    "referer": "https://www.challanpay.in/",
    "user-agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
}


class ExternalChallanClient:
    """
    ChallanPay D2C flow:
    1. POST user-verification → subscriber id, vehicle id, token
    2. GET find-challans?subscriberId=&vehicleId= with x-subscriber-token
    """

    def __init__(self):
        self.verify_url = settings.EXTERNAL_CHALLAN_API_URL
        self.find_url = settings.EXTERNAL_CHALLAN_FIND_URL
        self.utm_source = settings.EXTERNAL_CHALLAN_UTM_SOURCE
        self.timeout = settings.CHALLAN_FETCH_TIMEOUT_SECONDS
        self.max_retries = settings.CHALLAN_FETCH_MAX_RETRIES

    def fetch_challans(
        self,
        *,
        name: str,
        phone: str,
        vehicle_no: str,
        vehicle_type: str = "private",
    ) -> tuple[dict, int]:
        """Returns combined payload {verification, find_challans} and total duration_ms."""
        last_error: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            try:
                return self._fetch_two_step(name, phone, vehicle_no, vehicle_type)
            except ExternalAPIException as exc:
                last_error = exc
                if not self._is_retryable(exc) or attempt >= self.max_retries:
                    raise
                wait = 2**attempt
                logger.warning(
                    "Challan API retry",
                    extra={"extra_data": {"attempt": attempt, "wait_seconds": wait}},
                )
                time.sleep(wait)

        raise last_error or ExternalAPIException(message="Challan fetch failed")

    def _fetch_two_step(
        self, name: str, phone: str, vehicle_no: str, vehicle_type: str
    ) -> tuple[dict, int]:
        start = time.monotonic()
        verify_payload = {
            "name": name,
            "phone": phone,
            "vehicleNo": vehicle_no,
            "vehicleType": vehicle_type,
            "utmSource": self.utm_source,
        }

        verify_data, _ = self._post_json(self.verify_url, verify_payload, vehicle_no, step="verify")
        self._ensure_success(verify_data, step="user-verification")

        inner = verify_data.get("data") or {}
        subscriber = inner.get("subscriber") or {}
        vehicle = inner.get("vehicle") or {}
        token = inner.get("token") or ""

        subscriber_id = subscriber.get("id")
        vehicle_id = vehicle.get("id")
        if not subscriber_id or not vehicle_id or not token:
            raise ExternalAPIException(
                message="ChallanPay verification did not return subscriber, vehicle, or token",
                details={"keys": list(inner.keys())},
            )

        query = urlencode({"subscriberId": subscriber_id, "vehicleId": vehicle_id})
        find_url = f"{self.find_url}?{query}"
        find_headers = {**DEFAULT_HEADERS, "x-subscriber-token": token}
        find_data, _ = self._get_json(find_url, find_headers, vehicle_no, step="find-challans")
        self._ensure_success(find_data, step="find-challans")

        duration_ms = int((time.monotonic() - start) * 1000)
        combined = {
            "verification": verify_data,
            "find_challans": find_data,
            "subscriber_id": subscriber_id,
            "vehicle_id": vehicle_id,
            "vehicle_rc": (find_data.get("data") or {}).get("vehicle", {}),
        }
        return combined, duration_ms

    def _post_json(self, url: str, payload: dict, vehicle_no: str, step: str) -> tuple[dict, int]:
        correlation_id = get_correlation_id()
        start = time.monotonic()
        logger.info(
            "ChallanPay request",
            extra={"extra_data": {"step": step, "url": url, "vehicle": vehicle_no, "correlation_id": correlation_id}},
        )
        timeout = httpx.Timeout(self.timeout, connect=10.0)
        try:
            with httpx.Client(timeout=timeout, headers=DEFAULT_HEADERS) as client:
                response = client.post(url, json=payload)
                duration_ms = int((time.monotonic() - start) * 1000)
                return self._parse_response(response, step, duration_ms)
        except httpx.TimeoutException as exc:
            raise ExternalAPIException(message="Challan service timed out", details=str(exc)) from exc
        except httpx.RequestError as exc:
            raise ExternalAPIException(message="Unable to reach challan service", details=str(exc)) from exc

    def _get_json(self, url: str, headers: dict, vehicle_no: str, step: str) -> tuple[dict, int]:
        correlation_id = get_correlation_id()
        start = time.monotonic()
        logger.info(
            "ChallanPay request",
            extra={"extra_data": {"step": step, "url": url, "vehicle": vehicle_no, "correlation_id": correlation_id}},
        )
        timeout = httpx.Timeout(self.timeout, connect=10.0)
        try:
            with httpx.Client(timeout=timeout, headers=headers) as client:
                response = client.get(url)
                duration_ms = int((time.monotonic() - start) * 1000)
                return self._parse_response(response, step, duration_ms)
        except httpx.TimeoutException as exc:
            raise ExternalAPIException(message="Challan service timed out", details=str(exc)) from exc
        except httpx.RequestError as exc:
            raise ExternalAPIException(message="Unable to reach challan service", details=str(exc)) from exc

    def _parse_response(self, response: httpx.Response, step: str, duration_ms: int) -> tuple[dict, int]:
        logger.info(
            "ChallanPay response",
            extra={"extra_data": {"step": step, "status_code": response.status_code, "duration_ms": duration_ms}},
        )
        if response.status_code >= 500:
            raise ExternalAPIException(
                message="Challan service temporarily unavailable",
                details={"step": step, "status_code": response.status_code},
            )
        data = response.json() if response.content else {}
        if response.status_code >= 400:
            raise ExternalAPIException(
                message=data.get("message") or f"ChallanPay {step} failed",
                details={"step": step, "status_code": response.status_code, "body": data},
            )
        return data, duration_ms

    @staticmethod
    def _is_retryable(exc: ExternalAPIException) -> bool:
        details = exc.details if isinstance(exc.details, dict) else {}
        status_code = details.get("status_code")
        if isinstance(status_code, int) and status_code < 500:
            return False
        message = (exc.message or "").lower()
        return any(
            token in message
            for token in ("timed out", "temporarily unavailable", "unable to reach", "fetch failed")
        )

    @staticmethod
    def _ensure_success(data: dict, step: str) -> None:
        if ExternalChallanClient._is_empty_success(data, step):
            return

        status = str(data.get("status", "")).lower()
        success_flag = data.get("success")
        if success_flag is True:
            return
        if status in ("success", "ok", "200", "true"):
            return
        if status and status not in ("success", "ok"):
            message = str(data.get("message") or "").lower()
            if ExternalChallanClient._message_indicates_no_challans(message):
                return
            raise ExternalAPIException(
                message=data.get("message") or f"ChallanPay {step} returned error",
                details={"step": step, "response": data},
            )

    @staticmethod
    def _is_empty_success(data: dict, step: str) -> bool:
        """ChallanPay often returns HTTP 200 / success with zero challans — treat as valid."""
        if step != "find-challans":
            return False
        inner = data.get("data")
        if not isinstance(inner, dict):
            return False
        challans = inner.get("challans")
        if challans is None:
            return True
        if isinstance(challans, list) and len(challans) == 0:
            return True
        message = str(data.get("message") or "").lower()
        return ExternalChallanClient._message_indicates_no_challans(message)

    @staticmethod
    def _message_indicates_no_challans(message: str) -> bool:
        if not message:
            return False
        tokens = (
            "no challan",
            "no pending",
            "not found",
            "0 challan",
            "zero challan",
            "no record",
            "no data",
        )
        return any(token in message for token in tokens)
