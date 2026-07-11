import pytest
import os
from unittest.mock import patch, MagicMock
from src.infrastructure.aggregators.sql_aggregator import PostgresSqlAggregator

@patch("src.infrastructure.aggregators.sql_aggregator.psycopg2.connect")
@patch.dict(os.environ, {"DESTINATION__POSTGRES__CREDENTIALS": "postgresql://test:test@localhost/test"})
def test_postgres_sql_aggregator_success(mock_connect):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    
    # Setup context managers
    mock_connect.return_value.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    
    aggregator = PostgresSqlAggregator()
    aggregator.aggregate_table("test_source")
    
    assert mock_connect.called
    assert mock_conn.cursor.called
    assert mock_cursor.execute.called
    
    # Verify the SQL constructed correctly
    executed_query = mock_cursor.execute.call_args[0][0]
    assert "CREATE SCHEMA IF NOT EXISTS gold" in executed_query
    assert "CREATE TABLE gold.dim_test_source AS" in executed_query
    assert "SELECT * FROM silver.stg_test_source" in executed_query

@patch.dict(os.environ, {}, clear=True)
def test_postgres_sql_aggregator_missing_env():
    aggregator = PostgresSqlAggregator()
    with pytest.raises(ValueError, match="DESTINATION__POSTGRES__CREDENTIALS not set"):
        aggregator.aggregate_table("test_source")
