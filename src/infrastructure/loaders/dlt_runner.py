import json
from typing import Generator
import dlt
from src.domain.interfaces.loader import IDataLoader

class DltDataLoader(IDataLoader):
    def __init__(self, dataset_name: str = "bronze"):
        self.dataset_name = dataset_name

    def load_stream(self, table_name: str, stream: Generator[bytes, None, None]) -> None:
        def dict_generator():
            import zlib
            decompressor = zlib.decompressobj(32 + zlib.MAX_WBITS)
            buffer = ""
            is_gzip = None
            
            for chunk in stream:
                if is_gzip is None:
                    is_gzip = chunk.startswith(b'\x1f\x8b')
                
                try:
                    if is_gzip:
                        text_chunk = decompressor.decompress(chunk).decode('utf-8', errors='ignore')
                    else:
                        text_chunk = chunk.decode('utf-8', errors='ignore')
                except Exception:
                    # Ignore zlib/EOF errors if stream is artificially truncated by limit_mb
                    break
                    
                buffer += text_chunk
                
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    line = line.strip()
                    if line in ('[', ']', '') or line == ',':
                        continue
                    if line.endswith(','):
                        line = line[:-1]
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError:
                        continue

        pipeline = dlt.pipeline(
            pipeline_name="elite_bronze_pipeline",
            destination="postgres",
            dataset_name=self.dataset_name
        )
        pipeline.run(dict_generator(), table_name=table_name)
