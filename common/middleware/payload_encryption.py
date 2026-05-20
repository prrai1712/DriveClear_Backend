"""Encrypt/decrypt JSON API bodies so Network tab shows opaque payloads."""

from __future__ import annotations

import json
import logging

from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse

from common.crypto.payload_encryption import (
    PayloadEncryptionError,
    is_encrypted_envelope,
    unwrap_encrypted,
    wrap_encrypted,
)

logger = logging.getLogger("driveclear")

FETCH_PATH_SUFFIX = "/challans/fetch/"


class ApiPayloadEncryptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        if self._applies(request) and request.method in ("POST", "PUT", "PATCH"):
            blocked = self._decrypt_request(request)
            if blocked is not None:
                return blocked

        response = self.get_response(request)

        if not self._applies(request):
            return response

        content_type = response.get("Content-Type", "")
        if "application/json" not in content_type:
            return response

        try:
            return self._encrypt_response(response)
        except PayloadEncryptionError as exc:
            logger.exception("API payload encryption failed", extra={"error": str(exc)})
            return response

    def _config(self) -> tuple[bool, str, str]:
        enabled = bool(getattr(settings, "API_PAYLOAD_ENCRYPTION_ENABLED", False))
        key = getattr(settings, "API_PAYLOAD_ENCRYPTION_KEY", "") or ""
        scope = getattr(settings, "API_PAYLOAD_ENCRYPTION_SCOPE", "all") or "all"
        return enabled, key, scope

    def _applies(self, request: HttpRequest) -> bool:
        enabled, key, scope = self._config()
        if not enabled or not key:
            return False
        path = request.path or ""
        if not path.startswith("/api/v1/"):
            return False
        if path.startswith("/api/v1/auth/token/refresh"):
            return False
        if scope == "fetch_only":
            return path.endswith("/challans/fetch/") or FETCH_PATH_SUFFIX in path
        return True

    def _decrypt_request(self, request: HttpRequest) -> HttpResponse | None:
        _, key, _ = self._config()
        if not request.body:
            return None
        content_type = request.content_type or ""
        if "json" not in content_type:
            return None
        try:
            outer = json.loads(request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JsonResponse(
                {
                    "success": False,
                    "message": "Invalid JSON body",
                    "data": None,
                    "meta": {},
                    "error": {"code": "INVALID_PAYLOAD", "details": ""},
                },
                status=400,
            )
        if not isinstance(outer, dict) or not is_encrypted_envelope(outer):
            return JsonResponse(
                {
                    "success": False,
                    "message": "Encrypted payload required",
                    "data": None,
                    "meta": {},
                    "error": {"code": "ENCRYPTION_REQUIRED", "details": ""},
                },
                status=400,
            )
        try:
            inner = unwrap_encrypted(outer, key_b64=key)
        except PayloadEncryptionError:
            return JsonResponse(
                {
                    "success": False,
                    "message": "Could not decrypt request payload",
                    "data": None,
                    "meta": {},
                    "error": {"code": "DECRYPT_FAILED", "details": ""},
                },
                status=400,
            )
        request._body = json.dumps(inner).encode("utf-8")  # noqa: SLF001
        return None

    def _encrypt_response(self, response: HttpResponse) -> HttpResponse:
        _, key, _ = self._config()
        if not hasattr(response, "content") or not response.content:
            return response

        try:
            inner = json.loads(response.content.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return response

        if not isinstance(inner, dict) or is_encrypted_envelope(inner):
            return response

        outer = wrap_encrypted(inner, key_b64=key)
        encrypted = JsonResponse(outer, status=response.status_code, safe=False)
        for header, value in response.items():
            if header.lower() != "content-length":
                encrypted[header] = value
        encrypted["X-Payload-Encrypted"] = "1"
        return encrypted
