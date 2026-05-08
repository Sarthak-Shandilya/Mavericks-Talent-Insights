from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from configs.settings import get_settings

settings = get_settings()
_kwargs: dict = {"pool_pre_ping": True}
if settings.database_url.startswith("sqlite"):
    _kwargs = {"connect_args": {"check_same_thread": False}}
engine = create_engine(settings.database_url, **_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
