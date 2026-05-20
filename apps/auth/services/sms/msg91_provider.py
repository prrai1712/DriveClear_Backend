"""
MSG91 — real SMS OTP for India.
Sign up at https://msg91.com (free trial credits on new accounts).
"""
import logging

import httpx
from django.conf import settings

logger = logging.getLogger("driveclear")


class MSG91Provider:
    """Send OTP SMS via MSG91 HTTP API."""

    def send_otp(self, phone: str, otp: str) -> None:
        auth_key = settings.MSG91_AUTH_KEY
        sender = settings.MSG91_SENDER_ID
        template_id = settings.MSG91_TEMPLATE_ID

        if not auth_key:
            raise ValueError("MSG91_AUTH_KEY is not set in backend .env")

        # Indian mobile: 91XXXXXXXXXX
        mobile = f"91{phone}" if len(phone) == 10 else phone.lstrip("+")

        # Flow API (recommended) — requires OTP template in MSG91 dashboard
        if template_id:
            self._send_via_flow(auth_key, template_id, mobile, otp)
            return

        # Fallback: transactional route (simple text SMS)
        self._send_via_http(auth_key, sender, mobile, otp)

    def _send_via_flow(self, auth_key: str, template_id: str, mobile: str, otp: str) -> None:
        url = "https://control.msg91.com/api/v5/flow/"
        headers = {"authkey": auth_key, "Content-Type": "application/json"}
        payload = {
            "template_id": template_id,
            "short_url": "0",
            "recipients": [
                {
                    "mobiles": mobile,
                    "var": otp,  # match variable name in your MSG91 template e.g. ##var##
                    "otp": otp,
                }
            ],
        }
        with httpx.Client(timeout=15) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json() if response.content else {}
            if str(data.get("type", "")).lower() == "error":
                raise RuntimeError(data.get("message", "MSG91 flow error"))
        logger.info("MSG91 flow SMS sent", extra={"extra_data": {"mobile_suffix": mobile[-4:]}})

    def _send_via_http(self, auth_key: str, sender: str, mobile: str, otp: str) -> None:
        message = f"Your DriveClear verification code is {otp}. Valid for 5 minutes. Do not share."
        url = "https://control.msg91.com/api/sendhttp.php"
        params = {
            "authkey": auth_key,
            "mobiles": mobile,
            "message": message,
            "sender": sender or "DRCLEAR",
            "route": "4",
            "country": "91",
        }
        with httpx.Client(timeout=15) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            body = response.text.strip()
            # MSG91 returns message id on success
            if body and not body.isdigit() and "error" in body.lower():
                raise RuntimeError(body)
        logger.info("MSG91 HTTP SMS sent", extra={"extra_data": {"mobile_suffix": mobile[-4:]}})
