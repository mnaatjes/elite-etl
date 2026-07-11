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
    db_path = "elite_registry.db"
    if os.path.exists(db_path):
        os.remove(db_path)
        print("Deleted SQLite registry file.")
    else:
        # try the default sqlmodel path
        if os.path.exists("registry.db"):
            os.remove("registry.db")
            print("Deleted SQLite registry.db file.")
            
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
        
        # Silver
        print("Triggering Silver Normalization...")
        client.post(f"/api/v1/pipeline/silver/normalize/{source_id}")
        
        # Gold
        print("Triggering Gold Aggregation...")
        client.post(f"/api/v1/pipeline/gold/aggregate/{source_id}")
        
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

if __name__ == "__main__":
    clear_databases()
    # The models might need to be recreated for sqlite
    # If API crashes, we just run the FastAPI initialization again via TestClient
    from src.infrastructure.registry.database import init_db
    init_db()
    
    run_pipeline()
    inspect_tables()
