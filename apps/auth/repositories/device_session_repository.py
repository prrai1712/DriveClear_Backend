from django.utils import timezone

from apps.auth.models import DeviceSession
from common.database.base_repository import BaseRepository


class DeviceSessionRepository(BaseRepository):
    def touch(self, user_id: int, device_id: str, platform: str, ip: str) -> DeviceSession:
        session, _ = DeviceSession.objects.update_or_create(
            user_id=user_id,
            device_id=device_id,
            defaults={
                "platform": platform,
                "last_ip": ip or None,
                "last_seen_at": timezone.now(),
                "is_active": True,
            },
        )
        return session

    def deactivate_device(self, user_id: int, device_id: str) -> None:
        DeviceSession.objects.filter(user_id=user_id, device_id=device_id).update(is_active=False)

    def deactivate_all(self, user_id: int) -> None:
        DeviceSession.objects.filter(user_id=user_id).update(is_active=False)
