import pytest
from src.domain.lineage.models import HitLTemplate
from src.domain.lineage.parser import validate_and_extract_edges, SecurityViolationError, BoundaryViolationError

def test_valid_single_normalization():
    template = HitLTemplate(
        source_pipeline="spansh",
        target_layer="silver",
        raw_sql_string="CREATE TABLE stg_spansh_stations AS SELECT * FROM raw_spansh_stations;",
        submitted_by="admin"
    )
    edges = validate_and_extract_edges(template)
    assert len(edges) == 1
    assert edges[0].source_node_id == "raw_spansh_stations"
    assert edges[0].target_node_id == "stg_spansh_stations"
    assert edges[0].transformation_type == "DIRECT"

def test_valid_multiple_join_convergence():
    template = HitLTemplate(
        source_pipeline="global",
        target_layer="gold",
        raw_sql_string="""
            CREATE TABLE dim_stations_enriched AS 
            SELECT a.id, b.event 
            FROM stg_spansh_stations a
            JOIN stg_eddn_events b ON a.id = b.station_id;
        """,
        submitted_by="admin"
    )
    edges = validate_and_extract_edges(template)
    assert len(edges) == 2
    sources = {e.source_node_id for e in edges}
    assert sources == {"stg_spansh_stations", "stg_eddn_events"}
    assert edges[0].transformation_type == "JOIN"

def test_blanket_sql_rejection():
    template = HitLTemplate(
        source_pipeline="spansh",
        target_layer="silver",
        raw_sql_string="CREATE TABLE t1 AS SELECT * FROM r1; CREATE TABLE t2 AS SELECT * FROM r2;",
        submitted_by="admin"
    )
    with pytest.raises(SecurityViolationError, match="Multiple SQL statements detected"):
        validate_and_extract_edges(template)

def test_prohibited_ddl_rejection():
    template = HitLTemplate(
        source_pipeline="spansh",
        target_layer="silver",
        raw_sql_string="DROP TABLE raw_spansh_stations;",
        submitted_by="admin"
    )
    with pytest.raises(SecurityViolationError, match="Prohibited SQL operation detected"):
        validate_and_extract_edges(template)

def test_layer_skipping_rejection():
    template = HitLTemplate(
        source_pipeline="global",
        target_layer="gold",
        raw_sql_string="CREATE TABLE bad_gold AS SELECT * FROM raw_spansh_stations;",
        submitted_by="admin"
    )
    with pytest.raises(BoundaryViolationError, match="Layer Skipping detected"):
        validate_and_extract_edges(template)
