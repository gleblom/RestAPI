from typing import Annotated
import asyncio

from fastapi import Depends
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession

from src.config.main import Config

class Base(DeclarativeBase):
    pass

config = Config() # type: ignore

async_engine = create_async_engine(
    f"postgresql+asyncpg://{config.user}:{config.password.get_secret_value()}@{config.host}:{config.port}/{config.name}",
    echo=True, future=True)

DatabaseSession = async_sessionmaker(
    bind = async_engine, 
    expire_on_commit=False,
    class_= AsyncSession)

async def get_session():
    async with DatabaseSession() as session:
        yield session

SessionDep = Annotated[AsyncSession, Depends(get_session)]