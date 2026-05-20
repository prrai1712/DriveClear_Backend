import dj_database_url
from decouple import config

from .base import *  # noqa: F403

DEBUG = False
SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=True, cast=bool)
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Free Render tier: set USE_SQLITE=true when no external MySQL yet (ephemeral disk).
if config("USE_SQLITE", default=False, cast=bool):
    DATABASES["default"] = {  # noqa: F405
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",  # noqa: F405
    }
else:
    _database_url = config("DATABASE_URL", default="")
    if _database_url:
        DATABASES["default"] = dj_database_url.parse(  # noqa: F405
            _database_url,
            conn_max_age=600,
            conn_health_checks=True,
        )
    # Aiven MySQL requires TLS (ssl-mode=REQUIRED in connection URL).
    _db = DATABASES["default"]  # noqa: F405
    _host = str(_db.get("HOST", ""))
    _needs_ssl = config("DB_SSL", default=False, cast=bool) or "aivencloud.com" in _host
    if _needs_ssl:
        _opts = dict(_db.get("OPTIONS") or {})
        _opts.setdefault("charset", "utf8mb4")
        _opts.setdefault("init_command", "SET sql_mode='STRICT_TRANS_TABLES'")
        _opts["ssl_mode"] = "REQUIRED"
        _db["OPTIONS"] = _opts
