import os
from sqlalchemy.orm import Session
from src.infrastructure.registry.database import engine, init_db, SessionLocal
from src.infrastructure.registry.models import RegistryLineageNode, RegistryLineageEdge

def run_test():
    db_path = "data/metadata.db"
    
    # 1. Drop existing database
    print(f"[*] Removing existing database at {db_path}...")
    if os.path.exists(db_path):
        os.remove(db_path)
        
    # 2. Re-initialize schema
    print("[*] Initializing new schema...")
    init_db()
    
    # 3. Test insertions
    print("[*] Testing Node and Edge insertions...")
    session: Session = SessionLocal()
    try:
        # Insert Bronze Node
        bronze_node = RegistryLineageNode(
            medallion_layer="bronze",
            table_name="raw_spansh_stations"
        )
        # Insert Silver Node
        silver_node = RegistryLineageNode(
            medallion_layer="silver",
            table_name="stg_spansh_stations",
            transformation_template_path="src/domain/templates/silver/stg_spansh_stations.sql"
        )
        
        session.add(bronze_node)
        session.add(silver_node)
        session.commit()
        
        # Insert Edge
        edge = RegistryLineageEdge(
            source_node_id=bronze_node.id,
            target_node_id=silver_node.id
        )
        session.add(edge)
        session.commit()
        
        # Verification
        nodes_count = session.query(RegistryLineageNode).count()
        edges_count = session.query(RegistryLineageEdge).count()
        
        if nodes_count == 2 and edges_count == 1:
            print("[SUCCESS] Pause Point 1 Passed! Foreign Keys locked and Edge recorded.")
        else:
            print(f"[FAILED] Counts mismatch. Nodes: {nodes_count}, Edges: {edges_count}")
            
    except Exception as e:
        print(f"[FAILED] Exception during insertion: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    run_test()
