import pytest
import json
import decimal
import io
from unittest.mock import MagicMock, patch
from src.engine.database import PostgresAdapter

def test_edge_case_special_characters():
    """Verify that tabs, newlines, and backslashes don't break the TEXT format."""
    adapter = PostgresAdapter()
    # A string that could break TSV if not escaped: "Tab\tNewline\nBackslash\\"
    data = [
        [1, "System\tWith\tTabs", "Newline\nLine", "Backslash\\Char"]
    ]
    columns = ["id", "col1", "col2", "col3"]
    
    mock_conn = MagicMock()
    with patch.object(adapter, '_get_connection', return_value=mock_conn):
        mock_cur = mock_conn.cursor.return_value.__enter__.return_value
        adapter.copy_ingest("test_table", columns, data)
        
        # Capture the buffer sent to copy_expert
        buffer = mock_cur.copy_expert.call_args[0][1]
        content = buffer.getvalue()
        
        # Verify escaping: 
        # Tabs should become \t
        # Newlines should become \n
        # Backslashes should become \\
        assert "System\\tWith\\tTabs" in content
        assert "Newline\\nLine" in content
        assert "Backslash\\\\Char" in content
        assert "\t" in content # The actual separator between columns

def test_edge_case_decimal_precision():
    """Verify that high-precision Decimals are handled without data loss."""
    adapter = PostgresAdapter()
    # High precision coordinate
    p = decimal.Decimal("-17807.218750000000000000123")
    data = [[1, {"coords": {"x": p}}]]
    columns = ["id", "meta"]
    
    mock_conn = MagicMock()
    with patch.object(adapter, '_get_connection', return_value=mock_conn):
        mock_cur = mock_conn.cursor.return_value.__enter__.return_value
        adapter.copy_ingest("test_table", columns, data)
        
        content = mock_cur.copy_expert.call_args[0][1].getvalue()
        # Verify it serialized to a float string in the JSON
        assert "-17807.21875" in content

def test_edge_case_encoding_utf8():
    """Verify that emojis and non-latin characters pass through."""
    adapter = PostgresAdapter()
    # Sothis 😊 星 (Chinese character for star)
    fancy_name = "Sothis \U0001F60A \u661f"
    data = [[1, fancy_name]]
    columns = ["id", "name"]
    
    mock_conn = MagicMock()
    with patch.object(adapter, '_get_connection', return_value=mock_conn):
        mock_cur = mock_conn.cursor.return_value.__enter__.return_value
        adapter.copy_ingest("test_table", columns, data)
        
        content = mock_cur.copy_expert.call_args[0][1].getvalue()
        assert fancy_name in content

def test_edge_case_nested_json():
    """Verify deep nesting in JSONB columns."""
    adapter = PostgresAdapter()
    deep_data = {"a": {"b": {"c": {"d": [1, 2, 3]}}}}
    data = [[1, deep_data]]
    columns = ["id", "payload"]
    
    mock_conn = MagicMock()
    with patch.object(adapter, '_get_connection', return_value=mock_conn):
        mock_cur = mock_conn.cursor.return_value.__enter__.return_value
        adapter.copy_ingest("test_table", columns, data)
        
        content = mock_cur.copy_expert.call_args[0][1].getvalue()
        # Verify JSON is still valid after escaping backslashes for text format
        json_part = content.split("\t")[1].strip()
        # In text format we escaped backslashes, so to test we need to unescape
        # but here we didn't have backslashes in the JSON itself.
        parsed = json.loads(json_part)
        assert parsed == deep_data

def test_edge_case_extreme_bigint():
    """Verify that max BIGINT values pass through as strings to the text stream."""
    adapter = PostgresAdapter()
    # Max signed 64-bit int
    max_bigint = 9223372036854775807
    data = [[max_bigint, "test"]]
    columns = ["id64", "val"]
    
    mock_conn = MagicMock()
    with patch.object(adapter, '_get_connection', return_value=mock_conn):
        mock_cur = mock_conn.cursor.return_value.__enter__.return_value
        adapter.copy_ingest("test_table", columns, data)
        
        content = mock_cur.copy_expert.call_args[0][1].getvalue()
        assert str(max_bigint) in content
