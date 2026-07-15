from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.infrastructure.registry.database import init_db
from src.infrastructure.logging import setup_logging
from src.api.routers import sources, pipeline, jobs, catalog, analytics

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://192.168.1.146:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sources.router, prefix="/api/v1/sources", tags=["Sources"])
app.include_router(pipeline.router, prefix="/api/v1/pipeline", tags=["Pipeline Operations"])
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["Jobs"])
app.include_router(catalog.router, prefix="/api/v1/catalog", tags=["Catalog"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
