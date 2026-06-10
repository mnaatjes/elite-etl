import gzip
import json
from genson import SchemaBuilder
from src.adapters.base_analyzer import BaseAnalyzerAdapter

class JsonAnalyzerAdapter(BaseAnalyzerAdapter):
    """Adapter for inferring JSON schema from JSON or JSON Lines files."""

    def analyze(self, file_path: str, sample_size: int = 2000, sample_out_path: str = None) -> dict:
        builder = SchemaBuilder()
        sample_data = []
        
        # Determine if file is gzipped
        is_gz = file_path.endswith(".gz")
        open_func = gzip.open if is_gz else open
        
        count = 0
        try:
            with open_func(file_path, "rt", encoding="utf-8") as f:
                # Check if it's a JSON array or single object by peaking at first char
                first_char = f.read(1)
                f.seek(0)
                
                if first_char == "[":
                    # Potentially a large array
                    content = f.read()
                    try:
                        data = json.loads(content)
                        if isinstance(data, list):
                            sample_data = data[:sample_size]
                        else:
                            sample_data = [data]
                    except json.JSONDecodeError:
                        # Fallback for large arrays or malformed files: simple line reading
                        f.seek(0)
                        for line in f:
                            if count >= sample_size:
                                break
                            line = line.strip()
                            if not line or line == "[" or line == "]":
                                continue
                            if line.endswith(","):
                                line = line[:-1]
                            try:
                                item = json.loads(line)
                                sample_data.append(item)
                                count += 1
                            except json.JSONDecodeError:
                                continue
                else:
                    # Treat as JSON Lines or single object
                    for line in f:
                        if count >= sample_size:
                            break
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            item = json.loads(line)
                            sample_data.append(item)
                            count += 1
                        except json.JSONDecodeError:
                            # If first line fails, maybe it's the whole file as one object
                            if count == 0:
                                f.seek(0)
                                item = json.loads(f.read())
                                sample_data.append(item)
                                break
                            continue
                            
        except Exception as e:
            raise RuntimeError(f"Failed to analyze JSON file {file_path}: {str(e)}")
            
        # Add to builder and save sample if requested
        for item in sample_data:
            builder.add_object(item)
            
        if sample_out_path:
            with open(sample_out_path, "w", encoding="utf-8") as f:
                # We save the sample as a JSON array for easy viewing
                json.dump(sample_data, f, indent=4)
                
        return builder.to_schema()
