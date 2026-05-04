from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Maverick Talent Insights"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Local default: SQLite file in project dir. Switch to PostgreSQL via .env only:
    # DATABASE_URL=postgresql+psycopg2://user:pass@localhost:5432/mavericks
    database_url: str = "sqlite:///./mavericks.db"

    # JWT (set JWT_SECRET_KEY in production via .env)
    jwt_secret_key: str = "dev-only-change-me-use-openssl-rand-hex-32"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # One-time bootstrap when DB has zero users (optional; unset in production after first admin exists)
    bootstrap_admin_email: str | None = None
    bootstrap_admin_password: str | None = None
    bootstrap_admin_full_name: str | None = "System Administrator"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
