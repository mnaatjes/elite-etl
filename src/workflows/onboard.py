import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timezone

from src.engine.io import Downloader, StreamingIOAdapter
from src.engine.schema import Analyzer
from src.engine.resource import MemoryGuard
from src.engine.manifest import ManifestManager, DatasetEntry, ValidationState, DatasetMetadata, Timestamps
from src.engine.models import Source, SchemaContract, SyncJob
from src.engine.logger import logger, audit_log
from sqlalchemy.orm import Session

class OnboardingWorkflow:
    """
    Orchestrates Phase A: Data Onboarding with Tier 1 Validation.
    """
    def __init__(
        self, 
        db_session: Session, 
        manifest_mgr: ManifestManager,
        data_dir: Path,
        memory_limit: float = 75.0
    ):
        self.db = db_session
        self.manifest = manifest_mgr
        self.data_dir = data_dir
        self.sample_dir = data_dir / "samples"
        
        self.guard = MemoryGuard(limit_percent=memory_limit)
        self.downloader = Downloader(self.sample_dir)
        self.analyzer = Analyzer(memory_callback=self.guard.check_memory)

    def _sync_to_db(self, entry: DatasetEntry, source_id: int):
        job = self.db.query(SyncJob).filter_by(watermark=entry.id).first()
        if not job:
            job = SyncJob(source_id=source_id, watermark=entry.id)
            self.db.add(job)
        job.status = entry.status.lower()
        job.local_path = entry.local_filepath
        job.sha256 = entry.validation.actual_checksum
        job.byte_count = entry.metadata.file_size_bytes or 0
        if entry.timestamps.download_completed:
            job.finished_at = datetime.fromisoformat(entry.timestamps.download_completed)
        self.db.commit()

    def get_streaming_sample(self, url: str, sample_size_bytes: int = 2 * 1024 * 1024) -> StreamingIOAdapter:
        return self.downloader.stream_sample(url, byte_limit=sample_size_bytes)

    def analyze_source(self, source_input: Any, entry: Optional[DatasetEntry] = None) -> Dict[str, Any]:
        """
        Infers schema and performs Tier 1 validation.
        """
        logger.info("Workflow: Starting source analysis and Tier 1 validation")
        
        # 1. Infer
        raw_schema = self.analyzer.infer_schema(source_input)
        
        # 2. Get data for validation
        sample_data = self.analyzer.get_sample(source_input)
        
        # 3. Tier 1 Validation: Alignment Check
        if not self.analyzer.validate_alignment(raw_schema, sample_data):
            logger.warning("Workflow: Schema-Sample alignment suspect. Requesting deeper sample.")
            # We could trigger a recursive deep sample here, but for now we just log it.
            
        target_entry = entry or (source_input if isinstance(source_input, DatasetEntry) else None)
        if target_entry:
            target_entry.status = "ANALYZED"
            target_entry.timestamps.analysis_completed = datetime.now(timezone.utc).isoformat()
            self.manifest.add_entry(target_entry)
            source = self.db.query(Source).filter_by(name=target_entry.source_name).first()
            if source:
                self._sync_to_db(target_entry, source.id)
            audit_log("workflow_step_completed", step="analyze", source=target_entry.source_name, entry_id=target_entry.id)
                
        return raw_schema

    def prepare_hitl_yaml(self, name: str, raw_schema: Dict[str, Any]) -> Path:
        target_table = f"src_{name.lower().replace(' ', '_')}"
        yaml_content = self.analyzer.to_yaml(raw_schema, target_table)
        yaml_path = self.data_dir / "schemas" / f"{name.lower().replace(' ', '_')}_contract.yaml"
        with open(yaml_path, "w") as f:
            f.write(yaml_content)
        return yaml_path

    def finalize_onboarding(self, name: str, url: str, yaml_path: Path, raw_schema: Dict[str, Any]) -> Source:
        with open(yaml_path, "r") as f:
            approved_contract = self.analyzer.from_yaml(f.read())
        return self.register_source(
            name=name,
            url=url,
            target_table=approved_contract["target_table"],
            raw_schema=raw_schema,
            approved_schema=approved_contract["columns"]
        )

    def register_source(self, name: str, url: str, target_table: str, raw_schema: Dict[str, Any], approved_schema: Dict[str, Any]) -> Source:
        source = self.db.query(Source).filter_by(name=name).first()
        if not source:
            source = Source(name=name, url=url)
            self.db.add(source)
            self.db.flush()
        source.is_active = True
        contract = self.db.query(SchemaContract).filter_by(source_id=source.id).first()
        if not contract:
            contract = SchemaContract(source_id=source.id)
            self.db.add(contract)
        contract.target_table_name = target_table
        contract.raw_schema = raw_schema
        contract.approved_schema = approved_schema
        self.db.commit()
        audit_log("source_registered", source=name, target_table=target_table)
        return source
