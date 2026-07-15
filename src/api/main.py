from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.infrastructure.registry.database import init_db
from src.infrastructure.logging import setup_logging
from src.api.routers import sources, pipelines, dags, editor

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
app.include_router(pipelines.router, prefix="/api/v1/pipelines", tags=["Pipelines"])
app.include_router(dags.router, prefix="/api/v1/pipelines/{pipeline_id}/dags", tags=["DAG Configuration"])
app.include_router(editor.router, prefix="/api/v1/editor", tags=["BFF Workspace"])
