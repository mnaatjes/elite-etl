from rich.tree import Tree
from rich.console import Console

class NormalizationService:
    def __init__(self, console: Console = None):
        self.console = console or Console()

    def propose_normalization(self, raw_schema: dict) -> dict:
        """
        Analyzes raw JSON schema and proposes a relational/flat structure.
        Returns a target schema dictionary.
        """
        target_schema = {
            "table_name": "systems", # Default
            "columns": []
        }
        
        properties = raw_schema.get("properties", {})
        for field_name, props in properties.items():
            field_type = props.get("type")
            
            # Heuristic Rules
            if field_name == "coords" and field_type == "object":
                # Flatten coords
                for axis in ["x", "y", "z"]:
                    target_schema["columns"].append({
                        "name": f"coords_{axis}",
                        "source": f"coords.{axis}",
                        "type": "FLOAT",
                        "is_nullable": False
                    })
            elif "time" in field_name.lower() or "date" in field_name.lower():
                target_schema["columns"].append({
                    "name": field_name,
                    "source": field_name,
                    "type": "TIMESTAMP",
                    "is_nullable": True
                })
            elif field_type == "integer":
                target_schema["columns"].append({
                    "name": field_name,
                    "source": field_name,
                    "type": "BIGINT",
                    "is_nullable": False,
                    "is_pk": field_name == "id64"
                })
            else:
                target_schema["columns"].append({
                    "name": field_name,
                    "source": field_name,
                    "type": field_type.upper() if field_type else "TEXT",
                    "is_nullable": True
                })
        
        return target_schema

    def visualize_proposal(self, dataset_id: str, target_schema: dict):
        """Displays the proposed schema in a beautiful Tree structure."""
        tree = Tree(f"[bold cyan]Proposed Database Schema for {dataset_id}")
        
        table_node = tree.add(f"[bold yellow]Table: {target_schema['table_name']}")
        
        for col in target_schema["columns"]:
            pk_suffix = " [bold red](PK)[/bold red]" if col.get("is_pk") else ""
            type_info = f"[dim]{col['type']}[/dim]"
            source_info = f" [italic blue]<- {col['source']}[/italic blue]"
            table_node.add(f"{col['name']}{pk_suffix}: {type_info}{source_info}")
            
        self.console.print(tree)
