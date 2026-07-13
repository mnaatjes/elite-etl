import pytest
import os
from unittest.mock import patch, MagicMock, mock_open
from src.infrastructure.aggregators.sql_aggregator import PostgresSqlAggregator

@patch("builtins.open", new_callable=mock_open, read_data="CREATE TABLE gold.dim_test_source AS\nSELECT * FROM silver.stg_test_source")
@patch("src.infrastructure.aggregators.sql_aggregator.psycopg2.connect")
@patch.dict(os.environ, {"DESTINATION__POSTGRES__CREDENTIALS": "postgresql://test:test@localhost/test"})
def test_postgres_sql_aggregator_success(mock_connect, mock_file):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    
    # Setup context managers
    mock_connect.return_value.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    
    aggregator = PostgresSqlAggregator()
    aggregator.execute_template("test_source.sql")
    
    assert mock_connect.called
    assert mock_conn.cursor.called
    assert mock_cursor.execute.called
    
    # Verify the SQL constructed correctly
    calls = mock_cursor.execute.call_args_list
    schema_query = calls[0][0][0]
    table_query = calls[1][0][0]
    assert "CREATE SCHEMA IF NOT EXISTS gold" in schema_query
    assert "CREATE TABLE gold.dim_test_source AS" in table_query
    assert "SELECT * FROM silver.stg_test_source" in table_query

@patch.dict(os.environ, {}, clear=True)
def test_postgres_sql_aggregator_missing_env():
    aggregator = PostgresSqlAggregator()
    with pytest.raises(ValueError, match="DESTINATION__POSTGRES__CREDENTIALS not set"):
        aggregator.execute_template("test_source.sql")
