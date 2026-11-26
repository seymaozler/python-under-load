    
import asyncio
import time

from fastapi import APIRouter

router = APIRouter(prefix="/experiment", tags=["Experiments"])


@router.get("/async-io")
async def async_io():
    await asyncio.sleep(1)
    return {"message": "done"}


@router.get("/blocking-io")
async def blocking_io():
    time.sleep(1)
    return {"message": "done"}


@router.get("/sync-io")
def sync_io():
    time.sleep(1)
    return {"message": "done"}
