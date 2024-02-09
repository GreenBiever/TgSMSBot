from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from config import config
from .models import Base

DATABASE_URL = "mysql+aiomysql://{user}:{password}@{host}:{port}/{database}".format(**config["MySQL"])


engine = create_async_engine(DATABASE_URL, pool_recycle=1600)

async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

def get_conn() -> AsyncSession:
    return async_session()