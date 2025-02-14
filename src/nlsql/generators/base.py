from abc import ABC, abstractmethod
from typing import Dict, List, Any, Tuple
from sqlalchemy.engine import Inspector

class BaseQueryGenerator(ABC):
    """Abstract base class for SQL query generators."""
    
    @abstractmethod
    async def generate_query(
        self,
        query_text: str,
        inspector: Inspector,
        conversation_history: List[str],
        context: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Generate SQL query from natural language."""
        pass
    
    @abstractmethod
    async def validate_query(self, query: str) -> bool:
        """Validate generated SQL query."""
        pass