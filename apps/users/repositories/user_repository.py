from apps.users.models import User
from common.database.base_repository import BaseRepository


class UserRepository(BaseRepository):
    def get_by_phone(self, phone_number: str) -> User | None:
        return User.objects.filter(phone_number=phone_number).first()

    def get_by_id(self, user_id: int) -> User | None:
        return User.objects.filter(id=user_id).first()

    def create_or_update(self, phone_number: str, name: str) -> tuple[User, bool]:
        user, created = User.objects.get_or_create(
            phone_number=phone_number,
            defaults={"name": name},
        )
        if not created and name and user.name != name:
            user.name = name
            user.save(update_fields=["name", "updated_at"])
        return user, created

    def mark_phone_verified(self, user: User) -> User:
        user.is_phone_verified = True
        user.save(update_fields=["is_phone_verified", "updated_at"])
        return user
