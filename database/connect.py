from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine, Engine
from config import config
from .models import Base


def get_db_url(driver: str = 'aiomysql'):
    return "mysql+{driver}://{user}:{password}@{host}:{port}/{database}".format(
        **config["MySQL"], driver=driver)

engine = create_async_engine(get_db_url(), pool_recycle=1600)

async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def get_sync_engine() -> Engine:
    return create_engine(get_db_url(driver='pymysql'), pool_recycle=1600)


def get_sync_session(engine: Engine) -> Session:
    return Session(engine)