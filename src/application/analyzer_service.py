import json
import os
from pathlib import Path
from datetime import datetime
from src.ports.manifest_repository import ManifestRepository
from src.ports.data_analyzer import DataAnalyzerPort
from src.domain.manifest import DatasetManifest

class AnalyzerService:
    def __init__(self, manifest_repo: ManifestRepository, analyzer: DataAnalyzerPort):
        self.manifest_repo = manifest_repo
        self.analyzer = analyzer

    def extract_sample(self, dataset_id: str, sample_size: int = 2000) -> DatasetManifest:
        """Phase 1: Extracts sample and raw schema."""
        manifest = self.manifest_repo.get(dataset_id)
        if not manifest or not manifest.is_ready_for_analysis:
            raise RuntimeError(f"Dataset '{dataset_id}' not ready for sampling.")

        schema_dir = Path("data/schemas")
        schema_dir.mkdir(parents=True, exist_ok=True)
        sample_dir = Path("data/samples")
        sample_dir.mkdir(parents=True, exist_ok=True)
        
        raw_schema_path = schema_dir / f"{dataset_id}_raw_schema.json"
        sample_path = sample_dir / f"{dataset_id}_sample.json"

        schema = self.analyzer.analyze(
            manifest.local_filepath, 
            sample_size=sample_size, 
            sample_out_path=str(sample_path)
        )

        with open(raw_schema_path, "w", encoding="utf-8") as f:
            json.dump(schema, f, indent=4)

        manifest.status = "SAMPLED"
        manifest.metadata.schema_filepath = str(raw_schema_path)
        manifest.metadata.sample_filepath = str(sample_path)
        self.manifest_repo.save(manifest)
        return manifest

    def approve_schema(self, dataset_id: str) -> DatasetManifest:
        """Phase 4: Formalize schema and cleanup."""
        manifest = self.manifest_repo.get(dataset_id)
        if not manifest:
            raise ValueError(f"Dataset '{dataset_id}' not found.")

        target_schema_path = Path("data/schemas") / f"{dataset_id}_target_schema.json"
        if not target_schema_path.exists():
            raise FileNotFoundError(f"Target schema not found at {target_schema_path}. Run --normalize first.")

        # Cleanup sample
        if manifest.metadata.sample_filepath:
            sample_path = Path(manifest.metadata.sample_filepath)
            if sample_path.exists():
                sample_path.unlink()

        manifest.status = "READY_FOR_LOAD"
        manifest.validation.is_human_approved = True
        manifest.timestamps.analysis_completed = datetime.now()
        self.manifest_repo.save(manifest)
        return manifest
