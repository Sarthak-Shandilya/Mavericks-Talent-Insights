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

    # Upload + ingestion configuration
    queue_type: str = "in_memory"  # in_memory | activemq | service_bus
    queue_name_ingestion: str = "ingestion-uploads"
    queue_name_ingestion_completed: str = "ingestion-completed"

    activemq_host: str = "localhost"
    activemq_port: int = 61613
    activemq_user: str = ""
    activemq_password: str = ""
    activemq_destination_prefix: str = "/queue/"

    service_bus_connection_string: str = ""

    storage_type: str = "local"  # local | azure_blob
    local_storage_dir: str = "./uploads"
    azure_blob_connection_string: str = ""
    azure_blob_container: str = "mavericks-uploads"

    upload_max_file_size_mb: int = 25

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
