from abc import ABC, abstractmethod

class IDataAggregator(ABC):
    @abstractmethod
    def aggregate_table(self, source_name: str) -> None:
        """
        Models Silver staging tables into Gold facts and dimensions.
        """
        pass
