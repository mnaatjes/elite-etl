import pytest
from unittest.mock import MagicMock, patch
from src.engine.database import PostgresAdapter

def test_map_type():
    adapter = PostgresAdapter()
    assert adapter.map_type("string") == "TEXT"
    assert adapter.map_type("integer") == "BIGINT"
    assert adapter.map_type("boolean") == "BOOLEAN"
    assert adapter.map_type("object") == "JSONB"
    assert adapter.map_type("unknown") == "TEXT"

@patch("psycopg2.connect")
def test_create_table_sql(mock_connect):
    mock_conn = MagicMock()
    mock_connect.return_value = mock_conn
    mock_cur = mock_conn.cursor.return_value.__enter__.return_value
    
    adapter = PostgresAdapter()
    schema = {
        "id64": {"type": "integer", "name": "id64"},
        "name": {"type": "string", "name": "name"}
    }
    
    adapter.create_table("test_table", schema)
    
    # Verify that execute was called
    assert mock_cur.execute.called
    call_args = mock_cur.execute.call_args[0][0]
    # sql.SQL objects are hard to inspect directly, but we can check if they were passed
    assert "test_table" in str(call_args)
    assert "pipeline_id" in str(call_args)

@patch("psycopg2.connect")
def test_copy_ingest_interaction(mock_connect):
    mock_conn = MagicMock()
    mock_connect.return_value = mock_conn
    mock_cur = mock_conn.cursor.return_value.__enter__.return_value
    
    adapter = PostgresAdapter()
    columns = ["id", "val"]
    data = [[1, "a"], [2, "b"]]
    
    count = adapter.copy_ingest("test_table", columns, data)
    
    assert count == 2
    assert mock_cur.copy_expert.called
    assert mock_conn.commit.called
