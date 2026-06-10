from abc import ABC, abstractmethod

class FileDownloaderPort(ABC):
    """Port for streaming files from a URL to a local destination."""
    
    @abstractmethod
    def download(self, url: str, destination: str) -> str:
        """
        Streams file from url to destination.
        Returns the hex-encoded checksum (SHA-256) of the downloaded file.
        """
        pass
