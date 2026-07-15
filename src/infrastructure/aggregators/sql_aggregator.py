import os
import psycopg2
from src.domain.interfaces.aggregator import IDataAggregator
from src.infrastructure.logging import get_logger

logger = get_logger("aggregator.sql")

class PostgresSqlAggregator(IDataAggregator):
    def execute_sql(self, sql_template: str, layer: str = "gold") -> None:
        db_url = os.getenv("DESTINATION__POSTGRES__CREDENTIALS")
        if not db_url:
            raise ValueError("DESTINATION__POSTGRES__CREDENTIALS not set in environment")
            
        logger.info(f"Connecting to PostgreSQL to execute natively stored SQL template for layer: {layer}")
        
        try:
            with psycopg2.connect(db_url) as conn:
                with conn.cursor() as cur:
                    cur.execute(f"CREATE SCHEMA IF NOT EXISTS {layer};")
                    logger.debug(f"Executing Template Query:\n{sql_template}")
                    cur.execute(sql_template)
            logger.info("Execution complete for template.")
        except psycopg2.Error as e:
            logger.error(f"PostgreSQL execution failed: {e.pgerror or str(e)}")
            raise

    def validate_sql(self, sql: str) -> None:
        """Executes SQL in a transaction and rolls back to validate syntax and schema."""
        db_url = os.getenv("DESTINATION__POSTGRES__CREDENTIALS")
        if not db_url:
            raise ValueError("DESTINATION__POSTGRES__CREDENTIALS not set in environment")
            
        logger.info("Executing server-side validation (Dry Run)")
        try:
            with psycopg2.connect(db_url) as conn:
                conn.autocommit = False
                with conn.cursor() as cur:
                    cur.execute("CREATE SCHEMA IF NOT EXISTS silver;")
                    cur.execute("CREATE SCHEMA IF NOT EXISTS gold;")
                    cur.execute(sql)
                    conn.rollback()
                logger.info("Validation successful. Transaction rolled back.")
        except psycopg2.Error as e:
            logger.error(f"Validation failed: {e.pgerror or str(e)}")
            raise ValueError(f"SQL Validation Error: {e.pgerror or str(e)}")
