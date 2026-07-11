import pytest
import os
from unittest.mock import patch, MagicMock
from src.infrastructure.transformers.sql_transformer import PostgresSqlTransformer

@patch("src.infrastructure.transformers.sql_transformer.psycopg2.connect")
@patch.dict(os.environ, {"DESTINATION__POSTGRES__CREDENTIALS": "postgresql://test:test@localhost/test"})
def test_postgres_sql_transformer_success(mock_connect):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    
    # Setup context managers
    mock_connect.return_value.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    
    transformer = PostgresSqlTransformer()
    transformer.normalize_table("test_source")
    
    assert mock_connect.called
    assert mock_conn.cursor.called
    assert mock_cursor.execute.called
    
    # Verify the SQL constructed correctly
    executed_query = mock_cursor.execute.call_args[0][0]
    assert "CREATE SCHEMA IF NOT EXISTS silver" in executed_query
    assert "CREATE TABLE silver.stg_test_source AS" in executed_query
    assert "SELECT * FROM bronze.raw_test_source" in executed_query

@patch.dict(os.environ, {}, clear=True)
def test_postgres_sql_transformer_missing_env():
    transformer = PostgresSqlTransformer()
    with pytest.raises(ValueError, match="DESTINATION__POSTGRES__CREDENTIALS not set"):
        transformer.normalize_table("test_source")
