import os
import pandas as pd
from sqlalchemy import create_engine, text, MetaData, Table, Column, String, BigInteger, Float, DateTime, Boolean
from dotenv import load_dotenv
from typing import Iterable, Dict, Any

from src.ports.database_port import DatabasePort

class PostgresAdapter(DatabasePort):
    """SQLAlchemy/Postgres implementation of the Database Port."""

    def __init__(self):
        load_dotenv()
        user = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")
        host = os.getenv("DB_HOST")
        port = os.getenv("DB_PORT")
        db_name = os.getenv("DB_NAME")
        
        db_url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db_name}"
        self.engine = create_engine(db_url)
        self.metadata = MetaData()

    def create_table_from_schema(self, target_schema: dict) -> None:
        """Translates target_schema.json to a SQL table."""
        table_name = target_schema["table_name"]
        columns = []
        
        # Map our simplified string types to SQLAlchemy types
        type_map = {
            "BIGINT": BigInteger,
            "STRING": String,
            "TEXT": String,
            "FLOAT": Float,
            "TIMESTAMP": DateTime,
            "BOOLEAN": Boolean,
            "ARRAY": String, # Simple mapping for now
            "OBJECT": String # Simple mapping for now
        }

        for col_def in target_schema["columns"]:
            sql_type = type_map.get(col_def["type"], String)
            is_pk = col_def.get("is_pk", False)
            is_nullable = col_def.get("is_nullable", True)
            
            columns.append(Column(
                col_def["name"], 
                sql_type, 
                primary_key=is_pk, 
                nullable=is_nullable
            ))

        # Create the table object
        Table(table_name, self.metadata, *columns, extend_existing=True)
        
        # Physically create in Postgres
        self.metadata.create_all(self.engine)

    def load_data(self, table_name: str, data_generator: Iterable[dict], target_schema: dict) -> int:
        """Batch loads data using Pandas for performance."""
        total_rows = 0
        batch_size = 5000
        batch = []
        
        # Pre-calculate mapping for speed
        mapping = {col["name"]: col["source"] for col in target_schema["columns"]}

        def get_nested(data: dict, path: str):
            """Helper to extract nested values like coords.x"""
            parts = path.split('.')
            val = data
            for part in parts:
                if isinstance(val, dict) and part in val:
                    val = val[part]
                else:
                    return None
            return val

        for raw_record in data_generator:
            # Transform raw JSON record to flat SQL row
            processed_record = {}
            for col_name, source_path in mapping.items():
                processed_record[col_name] = get_nested(raw_record, source_path)
            
            batch.append(processed_record)
            
            if len(batch) >= batch_size:
                df = pd.DataFrame(batch)
                df.to_sql(table_name, self.engine, if_exists='append', index=False, method='multi')
                total_rows += len(batch)
                batch = []
        
        # Load final partial batch
        if batch:
            df = pd.DataFrame(batch)
            df.to_sql(table_name, self.engine, if_exists='append', index=False, method='multi')
            total_rows += len(batch)
            
        return total_rows
