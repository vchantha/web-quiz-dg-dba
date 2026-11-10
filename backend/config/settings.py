"""Environment-driven Django settings. All application records live in PostgreSQL."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
DEBUG = os.environ.get("DJANGO_DEBUG") == "1"
if not SECRET_KEY and not DEBUG:
    raise RuntimeError("Set DJANGO_SECRET_KEY in .env")
if not SECRET_KEY:
    SECRET_KEY = "dev-only-unsafe-secret-key-change-me"
# Public access by literal server IPv4/IPv6 is supported without knowing the IP at build time.
# A custom first middleware validates raw Host headers before accepting requests.
QUIZ_STATIC_ALLOWED_HOSTS = [
    x.strip() for x in os.environ.get(
        "DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,backend,testserver"
    ).split(",") if x.strip()
]
QUIZ_ALLOW_IP_HOSTS = os.environ.get("QUIZ_ALLOW_IP_HOSTS", "1") == "1"
# Django's built-in allowlist needs "*" to admit unknown IPs, so
# HostValidationMiddleware MUST validate each request against the explicit
# domain allowlist or a syntactically valid IP address.
ALLOWED_HOSTS = ["*"] if QUIZ_ALLOW_IP_HOSTS else QUIZ_STATIC_ALLOWED_HOSTS
CSRF_TRUSTED_ORIGINS = [x.strip() for x in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "http://localhost:8080").split(",") if x.strip()]
INSTALLED_APPS = [
    "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes",
    "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles",
    "assessment",
]
MIDDLEWARE = [
    "config.hosts.HostValidationMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "config.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [], "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.debug",
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]
WSGI_APPLICATION = "config.wsgi.application"
DATABASES = {"default": {
    "ENGINE": "django.db.backends.postgresql",
    "NAME": os.environ.get("POSTGRES_DB", "dba_quiz"),
    "USER": os.environ.get("POSTGRES_USER", "dba_quiz"),
    "PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
    "HOST": os.environ.get("DATABASE_HOST", "localhost"),
    "PORT": os.environ.get("DATABASE_PORT", "5432"),
    "CONN_MAX_AGE": 60,
}}
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Phnom_Penh"
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {"staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"}}
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE") == "1"
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = os.environ.get("CSRF_COOKIE_SECURE") == "1"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
QUIZ_MAX_ATTEMPTS = max(1, int(os.environ.get("QUIZ_MAX_ATTEMPTS", "1")))
QUIZ_SHOW_ANSWER_REVIEW = os.environ.get("QUIZ_SHOW_ANSWER_REVIEW") == "1"
