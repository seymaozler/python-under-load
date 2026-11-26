
import os

from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

router = APIRouter(
    prefix="/experiment",
    tags=["Database Experiments"],
)

engine = create_async_engine(
    os.environ["DATABASE_URL"],
    pool_size=10,
    max_overflow=0,
    pool_timeout=5,
)


@router.get("/db-hold")
async def db_hold():
    async with engine.connect() as connection:
        await connection.execute(
            text("SELECT pg_sleep(1)")
        )

    return {"status": "ok"}
