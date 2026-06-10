import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from src.engine.models import Base
from src.engine.manifest import ManifestManager
from src.engine.logger import setup_logger
from src.engine.database import PostgresAdapter

class EngineFactory:
    """
    Centralized factory for initializing engine components from environment/config.
    """
    def __init__(self, env_path: Optional[Path] = None):
        load_dotenv(env_path or Path(".env"), override=True)
        
        self.data_dir = Path(os.getenv("DATA_DIR", "data"))
        self.log_dir = Path(os.getenv("LOG_DIR", "logs"))
        self.metadata_db_url = os.getenv("METADATA_DB_URL", "sqlite:///data/metadata.db")
        
        # Ensure directories exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        (self.data_dir / "samples").mkdir(exist_ok=True)
        (self.data_dir / "downloads").mkdir(exist_ok=True)
        (self.data_dir / "schemas").mkdir(exist_ok=True)

        # Initialize Logging
        setup_logger(self.log_dir, level=os.getenv("LOG_LEVEL", "INFO"))

        # Initialize Database
        self.engine = create_engine(self.metadata_db_url)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def get_db(self) -> Session:
        return self.SessionLocal()

    def get_manifest_manager(self) -> ManifestManager:
        return ManifestManager(self.data_dir / "manifest.json")

    def get_postgres_adapter(self) -> PostgresAdapter:
        return PostgresAdapter()

    def get_data_dir(self) -> Path:
        return self.data_dir
