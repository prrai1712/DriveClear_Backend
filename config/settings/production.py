import dj_database_url
from decouple import config

from .base import *  # noqa: F403

DEBUG = False
SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=True, cast=bool)
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Render provides DATABASE_URL for MySQL/Postgres
_database_url = config("DATABASE_URL", default="")
if _database_url:
    DATABASES["default"] = dj_database_url.parse(  # noqa: F405
        _database_url,
        conn_max_age=600,
        conn_health_checks=True,
    )
