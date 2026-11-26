
from fastapi import APIRouter

router = APIRouter(
    prefix="/experiment",
    tags=["CPU Experiments"],
)


def cpu_work(n: int = 15_000_000) -> int:
    total = 0

    for i in range(n):
        total += i * i

    return total


@router.get("/cpu-async")
async def cpu_async():
    result = cpu_work()
    return {"result": result}


@router.get("/cpu-sync")
def cpu_sync():
    result = cpu_work()
    return {"result": result}
