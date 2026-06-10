from abc import ABC, abstractmethod

class DataAnalyzerPort(ABC):
    """Port for inferring schemas from data files."""
    
    @abstractmethod
    def analyze(self, file_path: str, sample_size: int = 2000, sample_out_path: str = None) -> dict:
        """
        Extracts a sample from file_path and returns an inferred JSON schema.
        If sample_out_path is provided, saves the extracted sample there.
        Supports both raw and compressed (.gz) files.
        """
        pass
