from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "sqlite:///./mavericks.db"

    queue_type: str = "generic"
    queue_name_ingestion: str = "ingestion-uploads"
    queue_name_ingestion_completed: str = "ingestion-completed"
    service_bus_connection_string: str = ""
    activemq_host: str = "localhost"
    activemq_port: int = 61613
    activemq_user: str = ""
    activemq_password: str = ""
    activemq_destination_prefix: str = "/queue/"

    storage_type: str = "local"
    local_storage_dir: str = "../../uploads"
    azure_blob_connection_string: str = ""
    azure_blob_container: str = "mavericks-uploads"

    ingestion_batch_size: int = 1000


@lru_cache
def get_settings() -> Settings:
    return Settings()
