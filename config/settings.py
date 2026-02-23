from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    APP_NAME: str = "rag-wp"
    API_KEY: str = "change-me"
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: str = "django-insecure-change-me-in-production"
    DEBUG: bool = True
    ALLOWED_HOSTS: list[str] = ["*"]

    # WordPress
    WP_BASE_URL: str
    WP_POSTS_PATH: str = "/wp-json/wp/v2/posts"
    WP_PER_PAGE: int = 100
    WP_USERNAME: str | None = None
    WP_APP_PASSWORD: str | None = None

    # DB
    DATABASE_URL: str

    # Redis / Celery
    REDIS_URL: str
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    # Chroma
    CHROMA_HOST: str = "chroma"
    CHROMA_PORT: int = 8000
    CHROMA_COLLECTION: str = "wp_posts"

    # RAG tuning
    CHUNK_SIZE: int = 1200
    CHUNK_OVERLAP: int = 180
    TOP_K: int = 6
    MAX_CONTEXT_CHUNKS: int = 6

    # Providers
    EMBEDDING_PROVIDER: str = "openai"
    LLM_PROVIDER: str = "openai"

    # OpenAI
    OPENAI_API_KEY: str | None = None
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_RESPONSES_MODEL: str = "gpt-5-mini"

    # Gemini
    GEMINI_API_KEY: str | None = None
    GEMINI_EMBEDDING_MODEL: str = "gemini-embedding-001"
    GEMINI_GENERATE_MODEL: str = "gemini-2.5-flash"


settings = Settings()

# Django Settings
SECRET_KEY = settings.SECRET_KEY
DEBUG = settings.DEBUG
ALLOWED_HOSTS = settings.ALLOWED_HOSTS

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'core',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database
import dj_database_url
DATABASES = {
    'default': dj_database_url.parse(settings.DATABASE_URL)
}

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS
CORS_ALLOW_ALL_ORIGINS = True

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'UNAUTHENTICATED_USER': None,
}
