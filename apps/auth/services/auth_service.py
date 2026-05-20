from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from apps.auth.repositories.device_session_repository import DeviceSessionRepository
from apps.auth.services.otp_service import OTPService
from apps.users.repositories.user_repository import UserRepository


class AuthService:
    def __init__(self):
        self.otp_service = OTPService()
        self.user_repo = UserRepository()
        self.device_repo = DeviceSessionRepository()

    def login_with_firebase(
        self,
        id_token: str,
        name: str = "",
        device_id: str = "",
        platform: str = "",
        ip_address: str | None = None,
    ) -> dict:
        """Verify Firebase phone-auth token and issue DriveClear JWT."""
        from apps.auth.services.firebase_service import FirebaseService

        firebase_user = FirebaseService().verify_id_token(id_token)
        phone = firebase_user["phone_number"]
        user, _ = self.user_repo.create_or_update(phone_number=phone, name=name)
        self.user_repo.mark_phone_verified(user)
        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])

        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        if device_id:
            session = self.device_repo.touch(user.id, device_id, platform, ip_address or "")
            session.refresh_token_jti = str(refresh.get("jti", ""))
            session.save(update_fields=["refresh_token_jti", "updated_at"])

        return {
            "access": str(access),
            "refresh": str(refresh),
            "user": {
                "uuid": str(user.uuid),
                "name": user.name,
                "phone_number": user.phone_number,
                "is_phone_verified": user.is_phone_verified,
            },
        }

    def send_otp(self, phone_number: str, name: str, ip_address: str | None = None) -> dict:
        if name:
            self.user_repo.create_or_update(phone_number=phone_number, name=name)
        return self.otp_service.send_otp(phone_number, ip_address)

    def verify_otp_and_login(
        self,
        phone_number: str,
        otp: str,
        name: str,
        device_id: str = "",
        platform: str = "",
        ip_address: str | None = None,
    ) -> dict:
        self.otp_service.verify_otp(phone_number, otp, ip_address)
        user, _ = self.user_repo.create_or_update(phone_number=phone_number, name=name)
        self.user_repo.mark_phone_verified(user)
        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])

        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        if device_id:
            session = self.device_repo.touch(user.id, device_id, platform, ip_address or "")
            session.refresh_token_jti = str(refresh.get("jti", ""))
            session.save(update_fields=["refresh_token_jti", "updated_at"])

        return {
            "access": str(access),
            "refresh": str(refresh),
            "user": {
                "uuid": str(user.uuid),
                "name": user.name,
                "phone_number": user.phone_number,
                "is_phone_verified": user.is_phone_verified,
            },
        }

    def logout(self, user_id: int, device_id: str = "") -> None:
        if device_id:
            self.device_repo.deactivate_device(user_id, device_id)
        else:
            self.device_repo.deactivate_all(user_id)

    def refresh_tokens(self, refresh_token_str: str) -> dict:
        refresh = RefreshToken(refresh_token_str)
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }
