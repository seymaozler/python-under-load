
from contextlib import asynccontextmanager

import anyio
from fastapi import FastAPI

from app.routes.io import router as experiment_router
from app.routes.database import router as database_router
from app.routes.cpu import router as cpu_router
from app.routes.concurrency import router as concurrency_router



@asynccontextmanager
async def lifespan(app: FastAPI):
    limiter = anyio.to_thread.current_default_thread_limiter()

    # Experiment only: reduce thread concurrency capacity.
    limiter.total_tokens = 40

    print(f"Thread limiter capacity: {limiter.total_tokens}")

    yield


app = FastAPI(
    title="Python Under Load",
    lifespan=lifespan,
)

app.include_router(experiment_router)
app.include_router(cpu_router)
app.include_router(database_router)
app.include_router(concurrency_router)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
