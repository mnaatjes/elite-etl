import json
import gzip
from datetime import datetime
from pathlib import Path
from src.ports.manifest_repository import ManifestRepository
from src.ports.database_port import DatabasePort
from src.domain.manifest import DatasetManifest

class LoaderService:
    def __init__(self, manifest_repo: ManifestRepository, db_adapter: DatabasePort):
        self.manifest_repo = manifest_repo
        self.db_adapter = db_adapter

    def load_dataset(self, dataset_id: str) -> DatasetManifest:
        """Phase 3: Orchestrates data loading into the database."""
        # 1. Fetch manifest and validate
        manifest = self.manifest_repo.get(dataset_id)
        if not manifest:
            raise ValueError(f"Dataset '{dataset_id}' not found.")
        
        if not manifest.validation.is_human_approved:
            raise RuntimeError(f"Dataset '{dataset_id}' is not approved for loading. Run --approve first.")

        # 2. Read approved target schema
        target_schema_path = Path("data/schemas") / f"{dataset_id}_target_schema.json"
        if not target_schema_path.exists():
            raise FileNotFoundError(f"Target schema not found at {target_schema_path}")
            
        with open(target_schema_path, "r") as f:
            target_schema = json.load(f)

        # 3. Prepare Database (Create/Update Table)
        self.db_adapter.create_table_from_schema(target_schema)

        # 4. Stream and Load Data
        rows_loaded = 0
        file_path = manifest.local_filepath
        is_gz = file_path.endswith(".gz")
        open_func = gzip.open if is_gz else open
        
        try:
            with open_func(file_path, "rt", encoding="utf-8") as f:
                # Generator for JSON records
                def json_generator():
                    # Handle both JSON array and JSON Lines
                    first_char = f.read(1)
                    f.seek(0)
                    
                    if first_char == "[":
                        # Standard JSON Array
                        data = json.load(f)
                        for item in data:
                            yield item
                    else:
                        # JSON Lines
                        for line in f:
                            line = line.strip()
                            if line:
                                yield json.loads(line)

                rows_loaded = self.db_adapter.load_data(
                    target_schema["table_name"], 
                    json_generator(), 
                    target_schema
                )
                
        except Exception as e:
            raise RuntimeError(f"Failed to load data from {file_path}: {str(e)}")

        # 5. Update Manifest
        manifest.status = "LOADED"
        manifest.timestamps.load_completed = datetime.now()
        manifest.metadata.estimated_rows = rows_loaded # Update with actual rows
        self.manifest_repo.save(manifest)

        return manifest
