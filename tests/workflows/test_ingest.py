import pytest
from unittest.mock import MagicMock, patch
from src.workflows.ingest import IngestionWorkflow
from src.engine.models import Source, SchemaContract

@pytest.fixture
def mock_db():
    return MagicMock()

@pytest.fixture
def mock_pg():
    return MagicMock()

@patch("src.workflows.ingest.ijson.items")
@patch("src.workflows.ingest.Downloader.stream_sample")
def test_ingest_source_logic(mock_stream, mock_ijson, mock_db, mock_pg):
    # Setup mock source and contract
    source = Source(id=1, name="Test Source", url="http://test.com")
    source.contract = SchemaContract(
        target_table_name="src_test",
        approved_schema={
            "id": {"name": "id", "type": "integer"},
            "val": {"name": "val", "type": "string"}
        }
    )
    mock_db.query.return_value.filter_by.return_value.first.return_value = source
    
    # Mock ijson to return test data
    mock_ijson.return_value = iter([
        {"id": 1, "val": "a"},
        {"id": 2, "val": "b"}
    ])
    
    # Mock postgres copy_ingest to return row count
    mock_pg.copy_ingest.return_value = 2
    
    workflow = IngestionWorkflow(mock_db, mock_pg)
    rows = workflow.ingest_source("Test Source")
    
    assert rows == 2
    assert mock_pg.copy_ingest.called
    # Check that data generator was passed and columns were correct
    args = mock_pg.copy_ingest.call_args[0]
    assert args[0] == "src_test"
    assert args[1] == ["id", "val"]
    
    # Verify SyncJob was created and updated
    assert mock_db.add.called
    assert mock_db.commit.called
