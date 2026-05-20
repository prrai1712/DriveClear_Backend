import dj_database_url
from decouple import config

from .base import *  # noqa: F403

DEBUG = True

# Optional: point local dev at Render/production MySQL (same DB as deployed API)
# Set DATABASE_URL in DriveClear_Backend/.env — overrides DB_HOST / DB_USER / etc.
_database_url = config("DATABASE_URL", default="")
if _database_url:
    DATABASES["default"] = dj_database_url.parse(  # noqa: F405
        _database_url,
        conn_max_age=600,
        conn_health_checks=True,
    )

SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = (  # noqa: F405
    "rest_framework.renderers.JSONRenderer",
    "rest_framework.renderers.BrowsableAPIRenderer",
)
