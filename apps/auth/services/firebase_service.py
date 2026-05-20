"""
Firebase — verify phone-auth ID tokens from web/mobile clients.

Priority: service account JSON → Auth emulator → google-auth + FIREBASE_PROJECT_ID.
"""
import json
import logging
import os
from pathlib import Path

from django.conf import settings

from common.exceptions.base import UnauthorizedException
from common.validators.phone import normalize_phone

logger = logging.getLogger("driveclear")

_initialized = False


def _get_firebase_modules():
    try:
        import firebase_admin
        from firebase_admin import auth as firebase_auth
        from firebase_admin import credentials
    except ImportError as exc:
        raise UnauthorizedException(
            message="firebase-admin not installed. Run: pip install -r requirements.txt",
            code="FIREBASE_NOT_CONFIGURED",
            details=str(exc),
        ) from exc
    return firebase_admin, firebase_auth, credentials


def _service_account_path() -> Path | None:
    cred_path = getattr(settings, "FIREBASE_CREDENTIALS_PATH", "") or ""
    if not cred_path:
        return None
    path = Path(cred_path)
    if not path.is_absolute():
        path = Path(settings.BASE_DIR) / path
    return path if path.is_file() else None


def _has_service_account() -> bool:
    if _service_account_path():
        return True
    return bool(getattr(settings, "FIREBASE_CREDENTIALS_JSON", "") or "")


def _auth_emulator_host() -> str:
    return (
        os.environ.get("FIREBASE_AUTH_EMULATOR_HOST", "").strip()
        or getattr(settings, "FIREBASE_AUTH_EMULATOR_HOST", "").strip()
    )


def _ensure_firebase_initialized() -> None:
    global _initialized
    firebase_admin, _, credentials = _get_firebase_modules()

    if _initialized or firebase_admin._apps:
        _initialized = True
        return

    emulator = _auth_emulator_host()
    project_id = getattr(settings, "FIREBASE_PROJECT_ID", "") or "demo-driveclear"

    if emulator:
        os.environ.setdefault("FIREBASE_AUTH_EMULATOR_HOST", emulator)
        firebase_admin.initialize_app(options={"projectId": project_id})
        _initialized = True
        logger.info("Firebase Admin initialized (auth emulator %s)", emulator)
        return

    path = _service_account_path()
    cred_json = getattr(settings, "FIREBASE_CREDENTIALS_JSON", "") or ""

    if path:
        cred = credentials.Certificate(str(path))
    elif cred_json:
        cred = credentials.Certificate(json.loads(cred_json))
    else:
        raise UnauthorizedException(
            message="Firebase service account not configured",
            code="FIREBASE_NOT_CONFIGURED",
        )

    firebase_admin.initialize_app(cred)
    _initialized = True
    logger.info("Firebase Admin initialized (service account)")


def _decode_claims(decoded: dict) -> dict:
    phone = decoded.get("phone_number")
    if not phone:
        raise UnauthorizedException(
            message="Phone number not found in Firebase token",
            code="FIREBASE_NO_PHONE",
        )
    return {
        "uid": decoded.get("uid") or decoded.get("sub"),
        "phone_number": normalize_phone(phone),
        "email": decoded.get("email"),
    }


def _verify_with_admin_sdk(id_token: str) -> dict:
    _, firebase_auth, _ = _get_firebase_modules()
    _ensure_firebase_initialized()
    decoded = firebase_auth.verify_id_token(id_token, check_revoked=True)
    return _decode_claims(decoded)


def _verify_with_google(id_token: str) -> dict:
    project_id = getattr(settings, "FIREBASE_PROJECT_ID", "") or ""
    if not project_id:
        raise UnauthorizedException(
            message="Set FIREBASE_PROJECT_ID in DriveClear_Backend/.env (e.g. driveclear-82af6)",
            code="FIREBASE_NOT_CONFIGURED",
        )

    from google.auth.transport import requests as google_requests
    from google.oauth2 import id_token as google_id_token

    try:
        decoded = google_id_token.verify_firebase_token(
            id_token,
            google_requests.Request(),
            audience=project_id,
        )
    except Exception as exc:
        logger.warning("Firebase token verification failed (google-auth)", exc_info=True)
        raise UnauthorizedException(
            message="Invalid or expired Firebase token",
            code="FIREBASE_TOKEN_INVALID",
            details=str(exc),
        ) from exc

    logger.debug("Firebase token verified via google-auth (project=%s)", project_id)
    return _decode_claims(decoded)


class FirebaseService:
    def verify_id_token(self, id_token: str) -> dict:
        try:
            if _auth_emulator_host() or _has_service_account():
                return _verify_with_admin_sdk(id_token)
            return _verify_with_google(id_token)
        except UnauthorizedException:
            raise
        except Exception as exc:
            logger.warning("Firebase token verification failed", exc_info=True)
            raise UnauthorizedException(
                message="Invalid or expired Firebase token",
                code="FIREBASE_TOKEN_INVALID",
                details=str(exc),
            ) from exc
