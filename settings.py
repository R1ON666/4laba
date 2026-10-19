import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-insecure-key-change-me")
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = ["*"] if DEBUG else ["127.0.0.1", "localhost"]

INSTALLED_APPS = ["django.contrib.messages"]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]
MESSAGE_STORAGE = "django.contrib.messages.storage.cookie.CookieStorage"

ROOT_URLCONF = "urls"

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"],
    "OPTIONS": {
        "context_processors": [
            "django.template.context_processors.request",
            "django.contrib.messages.context_processors.messages",
        ],
    },
}]

DATABASES = {}  # БД не нужна: данные хранятся в JSON-файлах

# Папка с JSON-файлами и ограничения
BOOKS_DIR = BASE_DIR / "data" / "books"
MAX_UPLOAD_SIZE = 1024 * 1024          # 1 МБ
MAX_BOOKS_PER_FILE = 1000
DATA_UPLOAD_MAX_MEMORY_SIZE = MAX_UPLOAD_SIZE * 2
FILE_UPLOAD_MAX_MEMORY_SIZE = MAX_UPLOAD_SIZE * 2

LANGUAGE_CODE = "ru"
TIME_ZONE = "Europe/Moscow"
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
