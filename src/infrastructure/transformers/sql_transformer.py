import os
import psycopg2
from src.domain.interfaces.transformer import IDataTransformer
from src.infrastructure.logging import get_logger

logger = get_logger("transformer.sql")

class PostgresSqlTransformer(IDataTransformer):
    def normalize_table(self, source_name: str) -> None:
        db_url = os.getenv("DESTINATION__POSTGRES__CREDENTIALS")
        if not db_url:
            raise ValueError("DESTINATION__POSTGRES__CREDENTIALS not set in environment")
            
        logger.info(f"Connecting to PostgreSQL for Silver normalization of {source_name}")
        
        raw_schema = "bronze"
        raw_table = f"raw_{source_name}"
        silver_schema = "silver"
        silver_table = f"stg_{source_name}"
        
        # In a full dbt implementation, this would be a templated macro.
        # For the prototype, we utilize raw SQL to demonstrate the Silver landing pattern.
        # This copies data from bronze, enabling schema changes without losing raw history.
        query = f"""
            CREATE SCHEMA IF NOT EXISTS {silver_schema};
            DROP TABLE IF EXISTS {silver_schema}.{silver_table};
            CREATE TABLE {silver_schema}.{silver_table} AS
            SELECT * FROM {raw_schema}.{raw_table};
        """
        
        try:
            with psycopg2.connect(db_url) as conn:
                with conn.cursor() as cur:
                    logger.debug(f"Executing Normalization Query:\n{query}")
                    cur.execute(query)
                # explicit commit is required outside the cursor but inside the connection, wait, psycopg2 context manager commits on exit automatically
            logger.info(f"Silver normalization complete: {silver_schema}.{silver_table}")
        except psycopg2.Error as e:
            logger.error(f"PostgreSQL execution failed: {e.pgerror or str(e)}")
            raise
