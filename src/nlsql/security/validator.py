import re
from typing import List, Set
from ..core.logging import setup_logging
from ..core.exceptions import SecurityError

logger = setup_logging(__name__)

class SQLSecurityValidator:
    """Validates SQL queries for security concerns."""
    
    def __init__(self):
        self.dangerous_patterns: List[str] = [
            r"\bDROP\b",
            r"\bDELETE\b",
            r"\bTRUNCATE\b",
            r"\bALTER\b",
            r"\bCREATE\b",
            r"\bINSERT\b",
            r"\bUPDATE\b",
            r"\bGRANT\b",
            r"\bREVOKE\b",
            r";.*$",  # Multiple statements
            r"/\*.*?\*/",  # Comments
            r"--.*$",  # Single line comments
            r"xp_.*",  # Extended stored procedures
            r"sp_.*",  # Stored procedures
        ]
        
        self.allowed_functions: Set[str] = {
            "COUNT", "SUM", "AVG", "MIN", "MAX",
            "ROUND", "FLOOR", "CEILING",
            "CONCAT", "SUBSTRING", "TRIM",
            "DATE", "EXTRACT", "TO_CHAR"
        }
    
    async def validate(self, query: str) -> bool:
        """
        Validate SQL query for security issues.
        
        Args:
            query: SQL query to validate
            
        Returns:
            True if query is safe, raises SecurityError otherwise
        """
        # Check for dangerous patterns
        for pattern in self.dangerous_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                raise SecurityError(f"Dangerous SQL pattern detected: {pattern}")
        
        # Validate function calls
        self._validate_functions(query)
        
        # Check query complexity
        self._validate_complexity(query)
        
        return True
    
    def _validate_functions(self, query: str):
        """Validate that only allowed functions are used."""
        # Extract function calls using regex
        function_pattern = r"\b([A-Za-z_]+)\s*\("
        functions = set(re.findall(function_pattern, query, re.IGNORECASE))
        
        # Check against allowed functions
        unknown_functions = {f.upper() for f in functions} - self.allowed_functions
        if unknown_functions:
            raise SecurityError(f"Unauthorized functions detected: {unknown_functions}")
    
    def _validate_complexity(self, query: str):
        """Validate query complexity to prevent DOS attacks."""
        # Check query length
        if len(query) > 5000:
            raise SecurityError("Query exceeds maximum length")
        
        # Check for too many joins
        join_count = len(re.findall(r"\bJOIN\b", query, re.IGNORECASE))
        if join_count > 10:
            raise SecurityError("Query contains too many JOIN operations")
        
        # Check for deep subqueries
        subquery_depth = query.count("SELECT") - 1
        if subquery_depth > 5:
            raise SecurityError("Query contains too many nested subqueries")
