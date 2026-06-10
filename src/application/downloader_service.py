import os
from datetime import datetime
from src.domain.manifest import DatasetManifest, ValidationState, Timestamps
from src.ports.manifest_repository import ManifestRepository
from src.ports.file_downloader import FileDownloaderPort

class DownloaderService:
    def __init__(self, manifest_repo: ManifestRepository, downloader: FileDownloaderPort):
        self.manifest_repo = manifest_repo
        self.downloader = downloader

    def download_dataset(self, dataset_id: str, source_uri: str, local_filepath: str = None, expected_checksum: str = None) -> DatasetManifest:
        """
        Orchestrates the download of a dataset and updates the manifest.
        """
        # 1. Check for idempotency BEFORE starting
        existing_manifest = self.manifest_repo.get(dataset_id)
        if existing_manifest and existing_manifest.status in ["DOWNLOADED", "SAMPLED", "NORMALIZATION_PROPOSED", "READY_FOR_LOAD"]:
            if os.path.exists(existing_manifest.local_filepath):
                # If we have a specific source_uri/local_filepath override, we might want to ignore idempotency
                # But for standard runs, we skip.
                return existing_manifest

        # 2. Handle automatic naming if no path provided
        if not local_filepath:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # Inferred extension from URI or default to .data
            ext = os.path.splitext(source_uri)[1] or ".data"
            local_filepath = f"data/downloads/{dataset_id}_{timestamp}{ext}"

        # 3. Initialize manifest entry
        manifest = DatasetManifest(
            id=dataset_id,
            source_uri=source_uri,
            local_filepath=local_filepath,
            status="DOWNLOADING"
        )
        manifest.timestamps.download_started = datetime.now()
        manifest.validation.expected_checksum = expected_checksum
        
        self.manifest_repo.save(manifest)

        # 4. Perform download
        try:
            actual_checksum = self.downloader.download(source_uri, local_filepath)
            
            # 5. Update manifest on success
            manifest.status = "DOWNLOADED"
            manifest.timestamps.download_completed = datetime.now()
            manifest.validation.actual_checksum = actual_checksum
            
            if expected_checksum:
                manifest.validation.passed_checksum = (actual_checksum == expected_checksum)
            else:
                # If no expected checksum was provided, we mark it as passed since we have a hash now
                manifest.validation.passed_checksum = True
            
            # 5. Set file to Read-Only (Immutability best practice)
            if os.path.exists(local_filepath):
                os.chmod(local_filepath, 0o440)
                
        except Exception as e:
            manifest.status = f"FAILED: {str(e)}"
            raise e
        finally:
            self.manifest_repo.save(manifest)

        return manifest
