import pytest
import gzip
from pathlib import Path
from src.engine.io import Downloader

def test_decompress_gz(tmp_path):
    download_dir = tmp_path / "downloads"
    downloader = Downloader(download_dir)
    
    gz_file = download_dir / "test.json.gz"
    content = b'{"test": "data"}'
    with gzip.open(gz_file, "wb") as f:
        f.write(content)
        
    decompressed = downloader.decompress_gz(gz_file)
    
    assert decompressed.suffix == ".json"
    assert decompressed.read_bytes() == content
    assert not gz_file.exists()

def test_engine_factory(tmp_path):
    from src.engine.factory import EngineFactory
    
    # Create a fake .env
    env_file = tmp_path / ".env"
    env_file.write_text(f'DATA_DIR={tmp_path}/data\nMETADATA_DB_URL=sqlite:///{tmp_path}/data/metadata.db')
    
    factory = EngineFactory(env_path=env_file)
    assert factory.data_dir == tmp_path / "data"
    assert (tmp_path / "data" / "samples").exists()
    
    db = factory.get_db()
    assert db is not None
    db.close()
