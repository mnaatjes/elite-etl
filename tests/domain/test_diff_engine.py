import pytest
from src.domain.catalog.diff_engine import SchemaDiffEngine
from src.domain.models.catalog import DiffType, DiffSeverity

def test_diff_engine_harmless_additive():
    # Upstream added 'age', SQL doesn't know about it
    compiled = {"id": "UUID", "name": "VARCHAR"}
    parent = {"id": "UUID", "name": "VARCHAR", "age": "INTEGER"}
    
    response = SchemaDiffEngine.calculate_diff(compiled, parent)
    
    assert not response.is_fatal
    assert len(response.diffs) == 1
    diff = response.diffs[0]
    assert diff.column_name == "age"
    assert diff.diff_type == DiffType.ADDITIVE
    assert diff.severity == DiffSeverity.WARNING

def test_diff_engine_fatal_subtractive():
    # Upstream dropped 'email', but SQL expects it
    compiled = {"id": "UUID", "email": "VARCHAR"}
    parent = {"id": "UUID"}
    
    response = SchemaDiffEngine.calculate_diff(compiled, parent)
    
    assert response.is_fatal
    assert len(response.diffs) == 1
    diff = response.diffs[0]
    assert diff.column_name == "email"
    assert diff.diff_type == DiffType.SUBTRACTIVE
    assert diff.severity == DiffSeverity.FATAL

def test_diff_engine_fatal_mutative():
    # Upstream changed 'id' type
    compiled = {"id": "INTEGER"}
    parent = {"id": "UUID"}
    
    response = SchemaDiffEngine.calculate_diff(compiled, parent)
    
    assert response.is_fatal
    assert len(response.diffs) == 1
    diff = response.diffs[0]
    assert diff.column_name == "id"
    assert diff.diff_type == DiffType.MUTATIVE
    assert diff.severity == DiffSeverity.FATAL

def test_diff_engine_clean():
    compiled = {"id": "UUID", "name": "VARCHAR"}
    parent = {"id": "UUID", "name": "VARCHAR"}
    
    response = SchemaDiffEngine.calculate_diff(compiled, parent)
    
    assert not response.is_fatal
    assert len(response.diffs) == 0
