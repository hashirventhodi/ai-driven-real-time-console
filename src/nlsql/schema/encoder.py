from sqlalchemy.engine import Inspector
from typing import Dict, List
import json
from ..core.logging import setup_logging

logger = setup_logging(__name__)

class SchemaEncoder:
    """Encodes database schema into a format suitable for LLM prompts."""
    
    async def encode(self, inspector: Inspector) -> str:
        """
        Encode database schema into a structured string.
        
        Args:
            inspector: SQLAlchemy inspector object
            
        Returns:
            Formatted schema string
        """
        schema_info = await self._collect_schema_info(inspector)
        return self._format_schema(schema_info)
    
    async def _collect_schema_info(self, inspector: Inspector) -> Dict:
        """Collect comprehensive schema information."""
        schema_info = {}
        
        for table_name in inspector.get_table_names():
            table_info = {
                "columns": [],
                "foreign_keys": [],
                "indexes": [],
                "primary_key": inspector.get_pk_constraint(table_name)
            }
            
            # Collect column information
            for column in inspector.get_columns(table_name):
                table_info["columns"].append({
                    "name": column["name"],
                    "type": str(column["type"]),
                    "nullable": column.get("nullable", True),
                    "default": str(column.get("default", "None"))
                })
            
            # Collect foreign keys
            for fk in inspector.get_foreign_keys(table_name):
                table_info["foreign_keys"].append({
                    "referred_table": fk["referred_table"],
                    "referred_columns": fk["referred_columns"],
                    "constrained_columns": fk["constrained_columns"]
                })
            
            # Collect indexes
            for idx in inspector.get_indexes(table_name):
                table_info["indexes"].append({
                    "name": idx["name"],
                    "columns": idx["column_names"],
                    "unique": idx["unique"]
                })
            
            schema_info[table_name] = table_info
        
        return schema_info
    
    def _format_schema(self, schema_info: Dict) -> str:
        """Format schema information into a clear string."""
        lines = []
        
        for table_name, info in schema_info.items():
            lines.append(f"\nTABLE: {table_name}")
            
            # Columns
            lines.append("COLUMNS:")
            for col in info["columns"]:
                col_str = f"  - {col['name']} ({col['type']})"
                if not col['nullable']:
                    col_str += " NOT NULL"
                if col['default'] != "None":
                    col_str += f" DEFAULT {col['default']}"
                lines.append(col_str)
            
            # Primary Key
            if info["primary_key"]["constrained_columns"]:
                pk_cols = ", ".join(info["primary_key"]["constrained_columns"])
                lines.append(f"PRIMARY KEY: ({pk_cols})")
            
            # Foreign Keys
            if info["foreign_keys"]:
                lines.append("FOREIGN KEYS:")
                for fk in info["foreign_keys"]:
                    lines.append(
                        f"  - {', '.join(fk['constrained_columns'])} → "
                        f"{fk['referred_table']}({', '.join(fk['referred_columns'])})"
                    )
            
            # Indexes
            if info["indexes"]:
                lines.append("INDEXES:")
                for idx in info["indexes"]:
                    unique_str = " UNIQUE" if idx["unique"] else ""
                    lines.append(
                        f"  - {idx['name']}{unique_str}: ({', '.join(idx['columns'])})"
                    )
        
        return "\n".join(lines)