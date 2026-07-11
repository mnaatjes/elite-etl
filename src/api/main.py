from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.infrastructure.registry.database import init_db
from src.infrastructure.logging import setup_logging
from src.api.routers import sources, pipeline

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging(log_dir="data/logs")
    init_db()
    yield
    # Shutdown

app = FastAPI(
    title="Elite Dangerous Data Pipeline",
    description="API for ETL Control Plane",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(sources.router, prefix="/api/v1/sources", tags=["Sources"])
app.include_router(pipeline.router, prefix="/api/v1/pipeline", tags=["Pipeline Operations"])
