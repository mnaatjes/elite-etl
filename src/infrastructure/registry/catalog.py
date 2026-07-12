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
        """Parses loader dict and registers all dynamically generated tables with their schemas."""
        logger.info(f"Cataloging generated tables for source {source_id} in layer {layer}")
        
        tables_data = load_info_dict.get("tables", [])
        
        for t_data in tables_data:
            if isinstance(t_data, str):
                # Fallback if old format
                t_name = t_data
                columns = None
            else:
                t_name = t_data.get("table_name")
                columns = t_data.get("columns")
                
            db_table = RegistrySourceTable(
                source_id=source_id,
                medallion_layer=layer,
                table_name=t_name,
                columns_schema=columns,
                row_count=0
            )
            self.session.add(db_table)
            
        self.session.commit()
        logger.info(f"Successfully cataloged {len(tables_data)} tables.")

    def get_tables(self, source_id: UUID, layer: str) -> List[str]:
        """Retrieves exactly which tables belong to a specific source in a specific layer."""
        tables = self.session.query(RegistrySourceTable).filter(
            RegistrySourceTable.source_id == source_id,
            RegistrySourceTable.medallion_layer == layer
        ).all()
        return [t.table_name for t in tables]
        
    def get_catalog(self, source_id: UUID, layer: str) -> dict:
        """Retrieves the full catalog payload including schema introspection for the source tables."""
        tables = self.session.query(RegistrySourceTable).filter(
            RegistrySourceTable.source_id == source_id,
            RegistrySourceTable.medallion_layer == layer
        ).all()
        
        tables_list = []
        for t in tables:
            tables_list.append({
                "table_name": t.table_name,
                "columns": t.columns_schema or []
            })
            
        return {
            "source_id": str(source_id),
            "layer": layer,
            "tables": tables_list
        }
        
    def update_template_path(self, source_id: UUID, layer: str, table_name: str, file_path: str) -> None:
        """Upserts a cataloged table with the reference pointer to its defining SQL template."""
        table = self.session.query(RegistrySourceTable).filter(
            RegistrySourceTable.source_id == source_id,
            RegistrySourceTable.medallion_layer == layer,
            RegistrySourceTable.table_name == table_name
        ).first()
        
        if table:
            table.transformation_template_path = file_path
        else:
            table = RegistrySourceTable(
                source_id=source_id,
                medallion_layer=layer,
                table_name=table_name,
                row_count=0,
                transformation_template_path=file_path
            )
            self.session.add(table)
            
        self.session.commit()
        logger.info(f"Updated template pointer for {layer}.{table_name}")

    def get_template_paths(self, source_id: UUID, layer: str) -> List[str]:
        """Retrieves all template paths registered for a specific source and layer."""
        tables = self.session.query(RegistrySourceTable).filter(
            RegistrySourceTable.source_id == source_id,
            RegistrySourceTable.medallion_layer == layer,
            RegistrySourceTable.transformation_template_path.isnot(None)
        ).all()
        return [t.transformation_template_path for t in tables]

    def get_lineage_graph(self, source_id: UUID) -> List[dict]:
        tables = self.session.query(RegistrySourceTable).filter(
            RegistrySourceTable.source_id == source_id
        ).all()
        
        graph = []
        for t in tables:
            graph.append({
                "layer": t.medallion_layer,
                "table_name": t.table_name,
                "template_path": t.transformation_template_path,
                "row_count": t.row_count
            })
            
        return graph
