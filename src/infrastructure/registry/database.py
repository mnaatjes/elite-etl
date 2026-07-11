from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.infrastructure.registry.models import Base

# SQLite database for the registry
SQLALCHEMY_DATABASE_URL = "sqlite:///data/metadata.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_registry_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
