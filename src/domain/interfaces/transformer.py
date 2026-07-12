from abc import ABC, abstractmethod

class IDataTransformer(ABC):
    @abstractmethod
    def execute_template(self, template_path: str, layer: str = "silver") -> None:
        """
        Executes a SQL template from the filesystem.
        """
        pass
        
    @abstractmethod
    def validate_sql(self, sql: str) -> None:
        """
        Validates a SQL string in a transaction.
        """
        pass
