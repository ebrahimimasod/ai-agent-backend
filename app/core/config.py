from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    APP_NAME: str = "rag-wp"
    API_KEY: str = "change-me"
    LOG_LEVEL: str = "INFO"

    # WordPress
    WP_BASE_URL: str
    WP_POSTS_PATH: str = "/wp-json/wp/v2/posts"
    WP_PER_PAGE: int = 100
    WP_MAX_POSTS: int = 0  # 0 means unlimited
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
    EMBEDDING_PROVIDER: str = "openai"  # openai|gemini
    LLM_PROVIDER: str = "openai"        # openai|gemini

    # OpenAI
    OPENAI_API_KEY: str | None = None
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_RESPONSES_MODEL: str = "gpt-5-mini"

    # Gemini
    GEMINI_API_KEY: str | None = None
    GEMINI_EMBEDDING_MODEL: str = "gemini-embedding-001"
    GEMINI_GENERATE_MODEL: str = "gemini-2.5-flash"


settings = Settings()
