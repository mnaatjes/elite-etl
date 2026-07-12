import os
import psycopg2
from typing import List
from src.infrastructure.logging import get_logger

logger = get_logger("database.inspector")

def get_active_tables(layer: str) -> List[str]:
    """Retrieves all active tables in a given PostgreSQL schema (layer)."""
    db_url = os.getenv("DESTINATION__POSTGRES__CREDENTIALS")
    if not db_url:
        raise ValueError("DESTINATION__POSTGRES__CREDENTIALS not set")
        
    query = f"""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = '{layer}' 
        AND table_type = 'BASE TABLE';
    """
    
    tables = []
    try:
        with psycopg2.connect(db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                results = cur.fetchall()
                tables = [row[0] for row in results]
    except psycopg2.Error as e:
        logger.error(f"Failed to inspect schema {layer}: {e}")
        
    return tables

def search_global_columns(query_str: str) -> List[dict]:
    """Performs a global search across bronze, silver, and gold schemas for matching tables or columns."""
    db_url = os.getenv("DESTINATION__POSTGRES__CREDENTIALS")
    if not db_url:
        raise ValueError("DESTINATION__POSTGRES__CREDENTIALS not set")
        
    query = """
        SELECT table_schema, table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_schema IN ('bronze', 'silver', 'gold')
        AND (table_name ILIKE %s OR column_name ILIKE %s)
        ORDER BY table_schema, table_name;
    """
    
    results = []
    search_pattern = f"%{query_str}%"
    
    try:
        with psycopg2.connect(db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(query, (search_pattern, search_pattern))
                rows = cur.fetchall()
                for row in rows:
                    results.append({
                        "schema": row[0],
                        "table_name": row[1],
                        "column_name": row[2],
                        "data_type": row[3]
                    })
    except psycopg2.Error as e:
        logger.error(f"Failed to execute global search for '{query_str}': {e}")
        
    return results
