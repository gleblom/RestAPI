from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from src.config.main import Config

settings = Config() # type: ignore

sync_engine = create_engine(
     f"postgresql://{settings.user}:{settings.password.get_secret_value()}@{settings.host}:{settings.port}/{settings.name}",  
    pool_pre_ping=True,
    pool_recycle=1800,
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=Session,
)