from abc import ABC, abstractmethod
from src.ports.data_analyzer import DataAnalyzerPort

class BaseAnalyzerAdapter(DataAnalyzerPort, ABC):
    """Abstract base class for all data analyzers (JSON, CSV, SQL, etc.)."""
    
    @abstractmethod
    def analyze(self, file_path: str, sample_size: int = 2000, sample_out_path: str = None) -> dict:
        pass
