import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


def env_list(name):
    return [x.strip() for x in os.environ.get(name, "").split(",") if x.strip()]


# --- Безопасность: на хостинге обязательно DJANGO_DEBUG=0 и свой DJANGO_SECRET_KEY ---
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "dev-only-insecure-key-change-me"
    else:
        raise ImproperlyConfigured("Задайте переменную окружения DJANGO_SECRET_KEY")

ALLOWED_HOSTS = ["127.0.0.1", "localhost"] + env_list("DJANGO_ALLOWED_HOSTS")
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")

INSTALLED_APPS = [
    "django.contrib.messages",
    "library",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]
MESSAGE_STORAGE = "django.contrib.messages.storage.cookie.CookieStorage"

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "APP_DIRS": True,
    "OPTIONS": {
        "context_processors": [
            "django.template.context_processors.request",
            "django.contrib.messages.context_processors.messages",
        ],
    },
}]

# SQLite. Путь можно переопределить (на хостинге храните файл в постоянной папке)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.environ.get("DJANGO_DB_PATH", BASE_DIR / "db.sqlite3"),
    }
}

# Папка с JSON-файлами и ограничения
BOOKS_DIR = Path(os.environ.get("BOOKS_DIR", BASE_DIR / "data" / "books"))
MAX_UPLOAD_SIZE = 1024 * 1024          # 1 МБ
MAX_BOOKS_PER_FILE = 1000
DATA_UPLOAD_MAX_MEMORY_SIZE = MAX_UPLOAD_SIZE * 2
FILE_UPLOAD_MAX_MEMORY_SIZE = MAX_UPLOAD_SIZE * 2

LANGUAGE_CODE = "ru"
TIME_ZONE = "Europe/Moscow"
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
