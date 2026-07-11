from typing import List
from uuid import UUID
from sqlalchemy.orm import Session
from src.domain.interfaces.catalog import ILineageCatalog
from src.infrastructure.registry.models import RegistrySourceTable
from src.infrastructure.logging import get_logger

logger = get_logger("registry.catalog")

class SqliteLineageCatalog(ILineageCatalog):
    def __init__(self, db_session: Session):
        self.session = db_session

    def register_tables(self, source_id: UUID, layer: str, load_info_dict: dict) -> None:
        """Parses DLT LoadInfo and registers all dynamically generated tables."""
        logger.info(f"Cataloging generated tables for source {source_id} in layer {layer}")
        
        # dlt load_info_dict contains 'load_packages', which is a list of packages
        # Each package has a 'jobs' dictionary containing table names and lists of jobs
        tables_seen = set()
        
        # This is robust parsing of dlt LoadInfo asdict() format
        for pkg in load_info_dict.get("load_packages", []):
            jobs = pkg.get("jobs", {})
            for job_category, table_jobs in jobs.items():
                for table_name in table_jobs:
                    # Ignore dlt internal tables if we only want business tables
                    if not table_name.startswith("_dlt"):
                        tables_seen.add(table_name)
                        
        if not tables_seen:
            # Fallback for if we use a different loader format or direct pass
            # Try to grab top-level "tables" list if we injected it
            tables_seen = set(load_info_dict.get("tables", []))
            
        for t_name in tables_seen:
            db_table = RegistrySourceTable(
                source_id=source_id,
                medallion_layer=layer,
                table_name=t_name,
                row_count=0  # Row count would be parsed if available
            )
            self.session.add(db_table)
            
        self.session.commit()
        logger.info(f"Successfully cataloged {len(tables_seen)} tables.")

    def get_tables(self, source_id: UUID, layer: str) -> List[str]:
        """Retrieves exactly which tables belong to a specific source in a specific layer."""
        tables = self.session.query(RegistrySourceTable).filter(
            RegistrySourceTable.source_id == source_id,
            RegistrySourceTable.medallion_layer == layer
        ).all()
        return [t.table_name for t in tables]
