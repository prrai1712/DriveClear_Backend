import uuid

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from apps.core.models.base import TimeStampedModel
from common.constants.enums import UserRole


class UserManager(models.Manager):
    def create_user(self, phone_number: str, name: str = "", **extra):
        user = self.model(phone_number=phone_number, name=name, **extra)
        user.set_unusable_password()
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    name = models.CharField(max_length=120, blank=True)
    phone_number = models.CharField(max_length=15, unique=True, db_index=True)
    is_phone_verified = models.BooleanField(default=False)
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.USER)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    last_login = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        db_table = "users"
        indexes = [
            models.Index(fields=["phone_number"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.name or 'User'} ({self.phone_number})"
