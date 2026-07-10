import sys
from fastapi.testclient import TestClient
from src.api.main import app
import os
from dotenv import load_dotenv

load_dotenv()

def run_e2e():
    with TestClient(app) as client:
        print("1. Registering Source: spansh_galaxy...")
        response = client.post("/api/v1/sources/", json={
            "name": "spansh_galaxy",
            "download_uri": "https://downloads.spansh.co.uk/galaxy_populated.json.gz",
            "schedule_interval_hours": 24
        })
        
        if response.status_code == 409:
            sources = client.get("/api/v1/sources/").json()
            source_id = next(s["id"] for s in sources if s["name"] == "spansh_galaxy")
            print(f"   Already exists. ID: {source_id}")
        elif response.status_code == 201:
            source_id = response.json()["id"]
            print(f"   Registered successfully! ID: {source_id}")
        else:
            print(f"   Failed to register: {response.text}")
            sys.exit(1)
            
        print("\n2. Approving Source for Ingestion...")
        response = client.put(f"/api/v1/sources/{source_id}/approve")
        if response.status_code != 200:
            print(f"   Failed to approve: {response.text}")
            sys.exit(1)
        print(f"   Approved. State: {response.json()['state']}")
        
        print("\n3. Triggering Bronze Sync (Network Stream -> DLT -> Postgres) with 10MB limit...")
        response = client.post(f"/api/v1/pipeline/bronze/sync/{source_id}", json={"limit_mb": 10})
        if response.status_code != 202:
            print(f"   Failed to sync: {response.text}")
            sys.exit(1)
            
        print(f"   Sync successful! Job ID: {response.json().get('job_id')}")

        print("\n4. Validating Postgres Tables created by DLT...")
        import psycopg2
        conn = psycopg2.connect(os.getenv("DESTINATION__POSTGRES__CREDENTIALS"))
        cur = conn.cursor()
        cur.execute("SELECT count(*) FROM bronze.raw_spansh_galaxy;")
        count = cur.fetchone()[0]
        print(f"   Total rows loaded into Postgres 'raw_spansh_galaxy' from the 10MB sample: {count}")
        print("\n5. Triggering Silver Normalization...")
        response = client.post(f"/api/v1/pipeline/silver/normalize/{source_id}")
        if response.status_code != 202:
            print(f"   Failed to normalize: {response.text}")
            sys.exit(1)
            
        print(f"   Normalization successful! Job ID: {response.json().get('job_id')}")
        
        print("\n6. Validating Postgres Staging Tables...")
        conn = psycopg2.connect(os.getenv("DESTINATION__POSTGRES__CREDENTIALS"))
        cur = conn.cursor()
        cur.execute("SELECT count(*) FROM silver.stg_spansh_galaxy;")
        count_silver = cur.fetchone()[0]
        print(f"   Total rows in 'silver.stg_spansh_galaxy': {count_silver}")
        print("\n7. Triggering Gold Aggregation...")
        response = client.post(f"/api/v1/pipeline/gold/aggregate/{source_id}")
        if response.status_code != 202:
            print(f"   Failed to aggregate: {response.text}")
            sys.exit(1)
            
        print(f"   Aggregation successful! Job ID: {response.json().get('job_id')}")
        
        print("\n8. Validating Postgres Gold Tables...")
        conn = psycopg2.connect(os.getenv("DESTINATION__POSTGRES__CREDENTIALS"))
        cur = conn.cursor()
        cur.execute("SELECT count(*) FROM gold.dim_spansh_galaxy;")
        count_gold = cur.fetchone()[0]
        print(f"   Total rows in 'gold.dim_spansh_galaxy': {count_gold}")
        conn.close()

if __name__ == "__main__":
    run_e2e()
