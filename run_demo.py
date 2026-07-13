import os
import sys
import psycopg2
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from src.api.main import app

load_dotenv()
pg_url = os.getenv("DESTINATION__POSTGRES__CREDENTIALS")

def clear_databases():
    print("--- 1. Clearing Databases ---")
    
    # SQLite
    db_paths = ["elite_registry.db", "registry.db", "data/metadata.db"]
    for db_path in db_paths:
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"Deleted SQLite registry file: {db_path}")
            
    # PostgreSQL
    try:
        conn = psycopg2.connect(pg_url)
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute("DROP SCHEMA IF EXISTS bronze CASCADE;")
        cur.execute("DROP SCHEMA IF EXISTS silver CASCADE;")
        cur.execute("DROP SCHEMA IF EXISTS gold CASCADE;")
        conn.close()
        print("Dropped Postgres schemas: bronze, silver, gold.")
    except Exception as e:
        print(f"Error dropping schemas: {e}")

def run_pipeline():
    print("\n--- 2. Running API Pipeline on galaxy_populated.json.gz (10MB limit) ---")
    with TestClient(app) as client:
        # Register
        print("Registering Source: spansh_systems...")
        response = client.post("/api/v1/sources/", json={
            "name": "spansh_systems",
            "download_uri": "https://downloads.spansh.co.uk/systems_1day.json.gz",
            "schedule_interval_hours": 24
        })
        if response.status_code == 201:
            source_id = response.json()["id"]
        else:
            print(f"Failed to register: {response.text}")
            return
            
        # Approve
        client.put(f"/api/v1/sources/{source_id}/approve")
        
        # Bronze
        print("Triggering Bronze Sync (limit 10MB)...")
        client.post(f"/api/v1/pipeline/bronze/sync/{source_id}", json={"limit_mb": 10})
        
        # Bronze Catalog (Schema Introspection)
        print("Retrieving Bronze Catalog with Schema Introspection...")
        response = client.get(f"/api/v1/pipeline/bronze/catalog/{source_id}")
        if response.status_code == 200:
            catalog_data = response.json()
            tables = catalog_data.get("tables", [])
            print(f"Catalog returned {len(tables)} tables.")
            if tables:
                first_table = tables[0]
                print(f"Sample Introspection for '{first_table.get('table_name')}':")
                for col in first_table.get("columns", [])[:3]:  # print first 3 columns
                    print(f"  - {col.get('name')} ({col.get('data_type')})")
        else:
            print(f"Failed to retrieve catalog: {response.text}")

        
        # Silver (HitL Dry Run & Execution)
        print("Triggering Silver Normalization (Dry Run & Execution)...")
        
        # Test dry_run failure
        print("  - Testing Invalid SQL Validation...")
        bad_payload = {
            "dry_run": True,
            "transformations": [
                {
                    "target_table": "stg_spansh_systems",
                    "sql": "SELECT non_existent_column FROM bronze.raw_spansh_systems;"
                }
            ]
        }
        res_bad = client.post(f"/api/v1/pipeline/silver/normalize/{source_id}", json=bad_payload)
        print(f"    Expected Failure Result: {res_bad.status_code}")
        
        # Test actual execution
        print("  - Executing Valid SQL Payload...")
        good_payload = {
            "dry_run": False,
            "transformations": [
                {
                    "target_table": "stg_spansh_systems",
                    "sql": "CREATE TABLE IF NOT EXISTS silver.stg_spansh_systems AS SELECT * FROM bronze.raw_spansh_systems;"
                }
            ]
        }
        res_good = client.post(f"/api/v1/pipeline/silver/normalize/{source_id}", json=good_payload)
        if res_good.status_code == 202:
            print(f"    Execution Result: {res_good.json()}")
        else:
            print(f"    Execution Failed: {res_good.text}")

        
        # Gold
        print("Triggering Gold Aggregation...")
        
        gold_payload = {
            "dry_run": False,
            "transformations": [
                {
                    "target_table": "dim_spansh_systems",
                    "sql": "CREATE TABLE IF NOT EXISTS gold.dim_spansh_systems AS SELECT * FROM silver.stg_spansh_systems;"
                }
            ]
        }
        res_gold = client.post(f"/api/v1/pipeline/gold/aggregate/{source_id}", json=gold_payload)
        if res_gold.status_code == 202:
            print(f"    Execution Result: {res_gold.json()}")
        else:
            print(f"    Execution Failed: {res_gold.text}")
            
        return source_id

def inspect_tables():
    print("\n--- 3. Inspecting PostgreSQL Tables ---")
    conn = psycopg2.connect(pg_url)
    cur = conn.cursor()
    
    query = """
    SELECT table_schema, table_name 
    FROM information_schema.tables 
    WHERE table_schema IN ('bronze', 'silver', 'gold')
    ORDER BY table_schema, table_name;
    """
    cur.execute(query)
    tables = cur.fetchall()
    
    print("\n[TABLE INVENTORY]")
    for schema, table in tables:
        # get row count
        cur.execute(f"SELECT count(*) FROM {schema}.{table};")
        count = cur.fetchone()[0]
        print(f"Schema: {schema.ljust(10)} | Table: {table.ljust(35)} | Rows: {count}")
        
def inspect_catalog():
    print("\n--- 4. Inspecting SQLite Data Lineage Catalog ---")
    import sqlite3
    try:
        conn = sqlite3.connect("data/metadata.db")
        cur = conn.cursor()
        cur.execute("SELECT medallion_layer, table_name FROM lineage_nodes ORDER BY table_name;")
        rows = cur.fetchall()
        print(f"\n[CATALOG INVENTORY: {len(rows)} Tables Registered]")
        for layer, name in rows:
            print(f"Layer: {layer.ljust(10)} | Table: {name}")
    except Exception as e:
        print(f"Could not inspect catalog: {e}")

def verify_dashboard_endpoints(source_id: str):
    print("\n--- 5. Verifying Dashboard UI Resource Endpoints ---")
    with TestClient(app) as client:
        # Sources
        print("Fetching /api/v1/sources/ ...")
        res_sources = client.get("/api/v1/sources/")
        if res_sources.status_code == 200:
            sources_data = res_sources.json()
            print(f"  Found {len(sources_data)} registered sources.")
        else:
            print(f"  Failed: {res_sources.text}")
        
        # Jobs
        print("Fetching /api/v1/jobs/ ...")
        res_jobs = client.get("/api/v1/jobs/")
        if res_jobs.status_code == 200:
            jobs_data = res_jobs.json()
            print(f"  Found {len(jobs_data)} job records.")
            if jobs_data:
                first_job_id = jobs_data[0]["id"]
                print(f"Fetching logs for job {first_job_id} ...")
                res_job_logs = client.get(f"/api/v1/jobs/{first_job_id}/logs")
                if res_job_logs.status_code == 200:
                    print("  Successfully retrieved specific job logs.")
                else:
                    print(f"  Failed to get job logs: {res_job_logs.text}")
        else:
            print(f"  Failed: {res_jobs.text}")
            
        # Lineage
        print(f"Fetching /api/v1/catalog/lineage/{source_id} ...")
        res_lineage = client.get(f"/api/v1/catalog/lineage/{source_id}")
        if res_lineage.status_code == 200:
            lineage_data = res_lineage.json()
            nodes_count = len(lineage_data.get('nodes', []))
            edges_count = len(lineage_data.get('edges', []))
            print(f"  Found {nodes_count} nodes and {edges_count} edges in the lineage graph.")
        else:
            print(f"  Failed: {res_lineage.text}")
            
        # Tables
        print("Fetching /api/v1/catalog/tables?layer=bronze ...")
        res_tables = client.get("/api/v1/catalog/tables?layer=bronze")
        if res_tables.status_code == 200:
            tables_data = res_tables.json()
            print(f"  Found {len(tables_data.get('tables', []))} active Bronze tables in PostgreSQL.")
        else:
            print(f"  Failed: {res_tables.text}")
            
        # Templates
        print(f"Fetching /api/v1/catalog/templates/{source_id}?layer=silver ...")
        res_templates = client.get(f"/api/v1/catalog/templates/{source_id}?layer=silver")
        if res_templates.status_code == 200:
            templates_data = res_templates.json()
            print(f"  Found {len(templates_data.get('templates', []))} SQL templates on filesystem.")
        else:
            print(f"  Failed: {res_templates.text}")

        # Analytics
        print("Fetching /api/v1/analytics/overview ...")
        res_analytics = client.get("/api/v1/analytics/overview")
        if res_analytics.status_code == 200:
            analytics_data = res_analytics.json()
            print(f"  Analytics: {analytics_data}")
        else:
            print(f"  Failed: {res_analytics.text}")

        # Search
        print("Fetching /api/v1/catalog/search?q=spansh ...")
        res_search = client.get("/api/v1/catalog/search?q=spansh")
        if res_search.status_code == 200:
            search_data = res_search.json()
            print(f"  Found {len(search_data.get('results', []))} search results for 'spansh'.")
        else:
            print(f"  Failed: {res_search.text}")

        # Patch Source
        print(f"Patching /api/v1/sources/{source_id} ...")
        res_patch = client.patch(f"/api/v1/sources/{source_id}", json={"schedule_interval_hours": 12})
        if res_patch.status_code == 200:
            patch_data = res_patch.json()
            print(f"  Patched source interval to: {patch_data.get('schedule_interval_hours')}")
        else:
            print(f"  Failed: {res_patch.text}")

if __name__ == "__main__":
    clear_databases()
    # The models might need to be recreated for sqlite
    # If API crashes, we just run the FastAPI initialization again via TestClient
    from src.infrastructure.registry.database import init_db
    init_db()
    
    source_id = run_pipeline()
    if source_id:
        inspect_tables()
        inspect_catalog()
        verify_dashboard_endpoints(source_id)
