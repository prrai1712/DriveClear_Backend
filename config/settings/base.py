"""
DriveClear — Base Django settings.
Split: local.py | production.py
"""
from datetime import timedelta
from pathlib import Path

from decouple import Csv, config

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=Csv())

# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
]

LOCAL_APPS = [
    "apps.core",
    "apps.users",
    "apps.auth.apps.AuthConfig",
    "apps.vehicles",
    "apps.challans",
    "apps.orders",
    "apps.payments",
    "apps.fulfilment",
    "apps.notifications",
    "apps.support",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "common.middleware.payload_encryption.ApiPayloadEncryptionMiddleware",
    "common.middleware.security.SecurityHeadersMiddleware",
    "common.middleware.request_logging.RequestLoggingMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "common.middleware.device_tracking.DeviceTrackingMiddleware",
    "common.middleware.rate_limiting.RateLimitMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "common.middleware.exception_handler.ExceptionMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

AUTH_USER_MODEL = "users.User"

# ---------------------------------------------------------------------------
# Database — MySQL only (local Docker: docker compose up -d)
# Schema source of truth: apps/*/models.py → python manage.py migrate
# ---------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": config("DB_NAME", default="driveclear"),
        "USER": config("DB_USER", default="root"),
        "PASSWORD": config("DB_PASSWORD", default=""),
        "HOST": config("DB_HOST", default="127.0.0.1"),
        "PORT": config("DB_PORT", default="3306"),
        "OPTIONS": {
            "charset": "utf8mb4",
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# ---------------------------------------------------------------------------
# Redis — cache, OTP, rate limiting (optional: use locmem if REDIS_URL unset)
# ---------------------------------------------------------------------------
REDIS_URL = config("REDIS_URL", default="")

if REDIS_URL:
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": REDIS_URL,
            "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
            "KEY_PREFIX": "dc",
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "driveclear",
        }
    }

# ---------------------------------------------------------------------------
# REST Framework + JWT
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
    ),
    "DEFAULT_PARSER_CLASSES": (
        "rest_framework.parsers.JSONParser",
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
    ),
    "EXCEPTION_HANDLER": "common.exceptions.handlers.drf_exception_handler",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": [],
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

# ---------------------------------------------------------------------------
# DriveClear business constants
# ---------------------------------------------------------------------------
ONLINE_CHALLAN_SERVICE_FEE_PAISE = 9900  # ₹99
COURT_SETTLEMENT_SERVICE_FEE_PAISE = 99900  # ₹999
CURRENCY = "INR"

OTP_LENGTH = 6
OTP_TTL_SECONDS = 300
OTP_MAX_ATTEMPTS = 5
OTP_RESEND_COOLDOWN_SECONDS = 60
OTP_DAILY_LIMIT_PER_PHONE = 10

VEHICLE_SEARCH_RATE_LIMIT = "20/hour"
CHALLAN_FETCH_TIMEOUT_SECONDS = 60
CHALLAN_FETCH_MAX_RETRIES = 2
CHALLAN_FETCH_CACHE_DAYS = config("CHALLAN_FETCH_CACHE_DAYS", default=3, cast=int)

# Application-layer AES-256-GCM for /api/v1 JSON (opaque in browser Network tab)
API_PAYLOAD_ENCRYPTION_ENABLED = config("API_PAYLOAD_ENCRYPTION_ENABLED", default=False, cast=bool)
API_PAYLOAD_ENCRYPTION_KEY = config("API_PAYLOAD_ENCRYPTION_KEY", default="")
# all | fetch_only
API_PAYLOAD_ENCRYPTION_SCOPE = config("API_PAYLOAD_ENCRYPTION_SCOPE", default="all")

EXTERNAL_CHALLAN_API_URL = config(
    "EXTERNAL_CHALLAN_API_URL",
    default="https://www.challanpay.in/api/d-to-c/user-verification",
)
EXTERNAL_CHALLAN_FIND_URL = config(
    "EXTERNAL_CHALLAN_FIND_URL",
    default="https://www.challanpay.in/api/d-to-c/find-challans",
)
EXTERNAL_CHALLAN_UTM_SOURCE = config("EXTERNAL_CHALLAN_UTM_SOURCE", default="challanpay")

RAZORPAY_KEY_ID = config("RAZORPAY_KEY_ID", default="")
RAZORPAY_KEY_SECRET = config("RAZORPAY_KEY_SECRET", default="")
RAZORPAY_WEBHOOK_SECRET = config("RAZORPAY_WEBHOOK_SECRET", default="")

SMS_PROVIDER = config("SMS_PROVIDER", default="mock")  # mock | msg91
MSG91_AUTH_KEY = config("MSG91_AUTH_KEY", default="")
MSG91_SENDER_ID = config("MSG91_SENDER_ID", default="DRCLEAR")
MSG91_TEMPLATE_ID = config("MSG91_TEMPLATE_ID", default="")  # optional Flow template ID

# Firebase — project ID required for token verify without service account JSON
FIREBASE_PROJECT_ID = config("FIREBASE_PROJECT_ID", default="")
FIREBASE_AUTH_EMULATOR_HOST = config("FIREBASE_AUTH_EMULATOR_HOST", default="")
FIREBASE_CREDENTIALS_PATH = config("FIREBASE_CREDENTIALS_PATH", default="")
FIREBASE_CREDENTIALS_JSON = config("FIREBASE_CREDENTIALS_JSON", default="")

# ---------------------------------------------------------------------------
# CORS / Security
# ---------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:3000",
    cast=Csv(),
)
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = (
    "accept",
    "authorization",
    "content-type",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
    "x-correlation-id",
    "x-device-id",
    "x-device-platform",
    "x-payload-encrypted",
)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

LANGUAGE_CODE = "en-in"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Logging — structured JSON in production
# ---------------------------------------------------------------------------
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {name} {correlation_id} {message}",
            "style": "{",
        },
        "json": {
            "()": "common.logging.formatters.JSONFormatter",
        },
    },
    "filters": {
        "correlation_id": {
            "()": "common.logging.filters.CorrelationIdFilter",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
            "filters": ["correlation_id"],
        },
        "file_app": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_DIR / "app.log",
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 10,
            "formatter": "json",
            "filters": ["correlation_id"],
        },
        "file_payment": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_DIR / "payments.log",
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 20,
            "formatter": "json",
            "filters": ["correlation_id"],
        },
        "file_external_api": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_DIR / "external_api.log",
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 20,
            "formatter": "json",
            "filters": ["correlation_id"],
        },
    },
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO"},
        "driveclear": {"handlers": ["console", "file_app"], "level": "INFO", "propagate": False},
        "driveclear.payments": {"handlers": ["console", "file_payment"], "level": "INFO", "propagate": False},
        "driveclear.external": {"handlers": ["console", "file_external_api"], "level": "INFO", "propagate": False},
    },
}

SPECTACULAR_SETTINGS = {
    "TITLE": "DriveClear API",
    "DESCRIPTION": "Indian traffic challan platform API",
    "VERSION": "1.0.0",
}
