from abc import ABC, abstractmethod

class IDataTransformer(ABC):
    @abstractmethod
    def normalize_table(self, source_name: str) -> None:
        """
        Normalizes a raw Bronze table into a Silver staging table.
        Should handle un-nesting, snake_casing, and type casting.
        """
        pass
