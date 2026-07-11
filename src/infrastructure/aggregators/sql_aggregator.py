import os
import psycopg2
from src.domain.interfaces.aggregator import IDataAggregator
from src.infrastructure.logging import get_logger

logger = get_logger("aggregator.sql")

class PostgresSqlAggregator(IDataAggregator):
    def aggregate_table(self, source_name: str) -> None:
        db_url = os.getenv("DESTINATION__POSTGRES__CREDENTIALS")
        if not db_url:
            raise ValueError("DESTINATION__POSTGRES__CREDENTIALS not set in environment")
            
        logger.info(f"Connecting to PostgreSQL for Gold aggregation of {source_name}")
        
        silver_schema = "silver"
        silver_table = f"stg_{source_name}"
        gold_schema = "gold"
        
        # We will build a dimension table for the source
        gold_table = f"dim_{source_name}"
        
        # In a full dbt implementation, this would be a modular macro.
        # For the Python prototype, we execute a generic structural aggregation
        # that bridges the staging table into a production dimension table.
        query = f"""
            CREATE SCHEMA IF NOT EXISTS {gold_schema};
            DROP TABLE IF EXISTS {gold_schema}.{gold_table};
            CREATE TABLE {gold_schema}.{gold_table} AS
            SELECT * FROM {silver_schema}.{silver_table};
        """
        
        try:
            with psycopg2.connect(db_url) as conn:
                with conn.cursor() as cur:
                    logger.debug(f"Executing Aggregation Query:\n{query}")
                    cur.execute(query)
            logger.info(f"Gold aggregation complete: {gold_schema}.{gold_table}")
        except psycopg2.Error as e:
            logger.error(f"PostgreSQL execution failed: {e.pgerror or str(e)}")
            raise
