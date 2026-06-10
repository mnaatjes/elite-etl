import psycopg2
from psycopg2 import sql
from typing import Dict, Any, List, Optional, Iterable, Union
import os
import io
import json
import decimal
from src.engine.logger import logger, audit_log

class PostgresAdapter:
    """
    Handles connections and DDL/DML operations for the PostgreSQL Data Warehouse.
    """
    def __init__(self):
        self.host = os.getenv("DB_HOST", "localhost")
        self.port = os.getenv("DB_PORT", "5432")
        self.user = os.getenv("DB_USER", "elite_db_role")
        self.password = os.getenv("DB_PASSWORD", "elite_danger_pass")
        self.dbname = os.getenv("DB_NAME", "elite_dangerous")
        self._conn = None

    def _get_connection(self):
        if self._conn is None or self._conn.closed:
            self._conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                dbname=self.dbname
            )
        return self._conn

    def execute(self, query: Union[str, sql.Composed], params: Optional[tuple] = None):
        conn = self._get_connection()
        with conn.cursor() as cur:
            cur.execute(query, params)
            conn.commit()

    def map_type(self, json_type: str) -> str:
        mapping = {
            "string": "TEXT",
            "integer": "BIGINT",
            "number": "DOUBLE PRECISION",
            "boolean": "BOOLEAN",
            "object": "JSONB",
            "array": "JSONB",
            "null": "TEXT"
        }
        return mapping.get(json_type.lower(), "TEXT")

    def validate_ddl(self, table_name: str, schema_contract: Dict[str, Any]) -> bool:
        """
        Tier 2 Validation: Performs a dry-run using a rolled-back transaction.
        """
        query = self._build_create_table_query(table_name, schema_contract)
        try:
            conn = self._get_connection()
            # We don't use conn.commit() here, we use rollback to undo the creation
            with conn.cursor() as cur:
                cur.execute(query)
            conn.rollback() # Undo the dry-run
            return True
        except Exception as e:
            logger.error(f"Tier 2 DDL Validation Failed for {table_name}: {e}")
            try: conn.rollback()
            except: pass
            return False

    def _build_create_table_query(self, table_name: str, schema_contract: Dict[str, Any]) -> sql.Composed:
        columns = []
        columns.append(sql.SQL("pipeline_id SERIAL PRIMARY KEY"))
        columns.append(sql.SQL("ingested_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP"))

        for col_id, details in schema_contract.items():
            col_name = details.get("name", col_id)
            col_type = self.map_type(details.get("type", "string"))
            columns.append(sql.SQL("{} {}").format(
                sql.Identifier(col_name),
                sql.SQL(col_type)
            ))

        return sql.SQL("CREATE TABLE {} ({})").format(
            sql.Identifier(table_name),
            sql.SQL(", ").join(columns)
        )

    def create_table(self, table_name: str, schema_contract: Dict[str, Any]):
        """
        Final execution of the CREATE TABLE command.
        """
        columns = []
        columns.append(sql.SQL("pipeline_id SERIAL PRIMARY KEY"))
        columns.append(sql.SQL("ingested_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP"))

        for col_id, details in schema_contract.items():
            col_name = details.get("name", col_id)
            col_type = self.map_type(details.get("type", "string"))
            columns.append(sql.SQL("{} {}").format(
                sql.Identifier(col_name),
                sql.SQL(col_type)
            ))

        query = sql.SQL("CREATE TABLE IF NOT EXISTS {} ({})").format(
            sql.Identifier(table_name),
            sql.SQL(", ").join(columns)
        )
        self.execute(query)

    def table_exists(self, table_name: str) -> bool:
        query = "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = %s)"
        conn = self._get_connection()
        with conn.cursor() as cur:
            cur.execute(query, (table_name,))
            return cur.fetchone()[0]

    def copy_ingest(self, table_name: str, columns: List[str], data_generator: Iterable[List[Any]]) -> int:
        conn = self._get_connection()
        count = 0
        query = sql.SQL("COPY {} ({}) FROM STDIN WITH (FORMAT TEXT, DELIMITER '\t', NULL '\\N')").format(
            sql.Identifier(table_name),
            sql.SQL(", ").join([sql.Identifier(c) for c in columns])
        )

        def decimal_default(obj):
            if isinstance(obj, decimal.Decimal): return float(obj)
            raise TypeError

        with conn.cursor() as cur:
            buffer = io.StringIO()
            for row in data_generator:
                formatted_row = []
                for val in row:
                    if val is None: formatted_row.append("\\N")
                    elif isinstance(val, (dict, list)):
                        js = json.dumps(val, default=decimal_default)
                        formatted_row.append(js.replace("\\", "\\\\"))
                    else:
                        s = str(val).replace("\\", "\\\\").replace("\t", "\\t").replace("\n", "\\n")
                        formatted_row.append(s)
                buffer.write("\t".join(formatted_row) + "\n")
                count += 1
                if count % 10000 == 0:
                    buffer.seek(0)
                    cur.copy_expert(query, buffer)
                    buffer = io.StringIO()
            if buffer.tell() > 0:
                buffer.seek(0)
                cur.copy_expert(query, buffer)
        conn.commit()
        return count

    def get_row_count(self, table_name: str) -> int:
        query = sql.SQL("SELECT count(*) FROM {}").format(sql.Identifier(table_name))
        conn = self._get_connection()
        with conn.cursor() as cur:
            cur.execute(query)
            return cur.fetchone()[0]

    def close(self):
        if self._conn and not self._conn.closed:
            self._conn.close()
