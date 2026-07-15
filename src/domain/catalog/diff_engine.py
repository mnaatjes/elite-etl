from typing import Dict, Any, List
from src.domain.models.catalog import SchemaDiffRequest, SchemaDiffResponse, ColumnDiff, DiffType, DiffSeverity

class SchemaDiffEngine:
    @staticmethod
    def calculate_diff(compiled_schema: Dict[str, str], parent_schema: Dict[str, str]) -> SchemaDiffResponse:
        """
        Calculates the schema drift between the compiled SQL template output and the known parent schema.
        Uses Python set operations for O(1) lookups.
        
        Args:
            compiled_schema: Dict mapping column name to type (what the SQL actually SELECTs)
            parent_schema: Dict mapping column name to type (what exists upstream)
        """
        compiled_cols = set(compiled_schema.keys())
        parent_cols = set(parent_schema.keys())
        
        diffs: List[ColumnDiff] = []
        is_fatal = False
        
        # Additive (New Column upstream not utilized by SQL, or explicitly added by SQL)
        added_upstream = parent_cols - compiled_cols
        for col in added_upstream:
            diffs.append(ColumnDiff(
                column_name=col,
                diff_type=DiffType.ADDITIVE,
                severity=DiffSeverity.WARNING,
                message=f"Warning: Upstream added column '{col}'. Ignored by current SQL."
            ))
            
        # Subtractive (SQL expects it, but upstream dropped it)
        dropped_upstream = compiled_cols - parent_cols
        for col in dropped_upstream:
            # If the SQL expects it but it's not upstream, this is a FATAL execution blocker.
            is_fatal = True
            diffs.append(ColumnDiff(
                column_name=col,
                diff_type=DiffType.SUBTRACTIVE,
                severity=DiffSeverity.FATAL,
                message=f"FATAL: Column '{col}' referenced in SQL but missing upstream."
            ))
            
        # Mutative (Type clashes)
        shared_cols = compiled_cols & parent_cols
        for col in shared_cols:
            comp_type = compiled_schema[col].upper()
            parent_type = parent_schema[col].upper()
            if comp_type != parent_type:
                is_fatal = True
                diffs.append(ColumnDiff(
                    column_name=col,
                    diff_type=DiffType.MUTATIVE,
                    severity=DiffSeverity.FATAL,
                    message=f"FATAL: Type mismatch for '{col}'. SQL expects {comp_type}, but upstream is {parent_type}."
                ))
                
        return SchemaDiffResponse(
            is_fatal=is_fatal,
            diffs=diffs
        )
