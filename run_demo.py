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
        print("Registering Source: spansh_populated...")
        response = client.post("/api/v1/sources/", json={
            "name": "spansh_populated",
            "download_uri": "https://downloads.spansh.co.uk/galaxy_populated.json.gz",
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
                    "target_table": "stg_spansh_populated",
                    "sql": "SELECT non_existent_column FROM bronze.raw_spansh_populated;"
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
                    "target_table": "stg_spansh_populated",
                    "sql": "CREATE TABLE IF NOT EXISTS silver.stg_spansh_populated AS SELECT * FROM bronze.raw_spansh_populated;"
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
                    "target_table": "dim_spansh_populated",
                    "sql": "CREATE TABLE IF NOT EXISTS gold.dim_spansh_populated AS SELECT * FROM silver.stg_spansh_populated;"
                }
            ]
        }
        res_gold = client.post(f"/api/v1/pipeline/gold/aggregate/{source_id}", json=gold_payload)
        if res_gold.status_code == 202:
            print(f"    Execution Result: {res_gold.json()}")
        else:
            print(f"    Execution Failed: {res_gold.text}")
        
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
        cur.execute("SELECT medallion_layer, table_name FROM source_tables ORDER BY table_name;")
        rows = cur.fetchall()
        print(f"\n[CATALOG INVENTORY: {len(rows)} Tables Registered]")
        for layer, name in rows:
            print(f"Layer: {layer.ljust(10)} | Table: {name}")
    except Exception as e:
        print(f"Could not inspect catalog: {e}")

if __name__ == "__main__":
    clear_databases()
    # The models might need to be recreated for sqlite
    # If API crashes, we just run the FastAPI initialization again via TestClient
    from src.infrastructure.registry.database import init_db
    init_db()
    
    run_pipeline()
    inspect_tables()
    inspect_catalog()
