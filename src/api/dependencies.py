from fastapi import Depends
from sqlalchemy.orm import Session
from src.infrastructure.registry.database import get_registry_session
from src.infrastructure.registry.repository import SQLiteRegistryRepository
from src.domain.interfaces.registry import IRegistryRepository
from src.domain.interfaces.catalog import ILineageCatalog
from src.infrastructure.registry.catalog import SqliteLineageCatalog

def get_registry_repository(session: Session = Depends(get_registry_session)) -> IRegistryRepository:
    return SQLiteRegistryRepository(session)

def get_lineage_catalog(session: Session = Depends(get_registry_session)) -> ILineageCatalog:
    return SqliteLineageCatalog(session)
