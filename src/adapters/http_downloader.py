import httpx
import hashlib
from pathlib import Path
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn

from src.ports.file_downloader import FileDownloaderPort

class HttpDownloaderAdapter(FileDownloaderPort):
    """HTTP implementation of FileDownloaderPort using httpx and rich for progress."""

    def download(self, url: str, destination: str) -> str:
        dest_path = Path(destination)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        sha256 = hashlib.sha256()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            "•",
            TimeRemainingColumn(),
        ) as progress:
            
            with httpx.stream("GET", url, follow_redirects=True) as response:
                response.raise_for_status()
                
                total_size = int(response.headers.get("Content-Length", 0))
                task = progress.add_task(f"[cyan]Downloading {dest_path.name}...", total=total_size)
                
                with open(dest_path, "wb") as f:
                    try:
                        for chunk in response.iter_bytes(chunk_size=16384):
                            f.write(chunk)
                            sha256.update(chunk)
                            progress.update(task, advance=len(chunk))
                    except (Exception, KeyboardInterrupt) as e:
                        # Close the file and remove partial download
                        f.close()
                        if dest_path.exists():
                            dest_path.unlink()
                        raise e
        
        return sha256.hexdigest()
