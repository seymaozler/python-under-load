
import asyncio

from fastapi import APIRouter, HTTPException

router = APIRouter(
    prefix="/experiment",
    tags=["Concurrency Experiments"],
)

MAX_ACTIVE = 10

semaphore = asyncio.Semaphore(MAX_ACTIVE)
counter_lock = asyncio.Lock()
active_requests = 0


async def simulated_downstream():
    global active_requests

    async with counter_lock:
        active_requests += 1
        current_active = active_requests

    try:
        if current_active > MAX_ACTIVE:
            raise HTTPException(
                status_code=503,
                detail="Simulated downstream overloaded",
            )

        await asyncio.sleep(1)
        return {"status": "ok"}

    finally:
        async with counter_lock:
            active_requests -= 1


@router.get("/downstream-unbounded")
async def unbounded():
    return await simulated_downstream()


@router.get("/downstream-bounded")
async def bounded():
    async with semaphore:
        return await simulated_downstream()
