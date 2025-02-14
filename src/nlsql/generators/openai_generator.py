from typing import Dict, List, Any, Tuple, Optional
from openai import OpenAI
from sqlalchemy.engine import Inspector
import asyncio
import json

from ..core.config import get_settings
from ..core.logging import setup_logging
from ..core.exceptions import QueryGenerationError
from .base import BaseQueryGenerator
from ..schema.encoder import SchemaEncoder
from ..security.validator import SQLSecurityValidator
from ..visualization.analyzer import VisualizationAnalyzer

logger = setup_logging(__name__)

class OpenAIGenerator(BaseQueryGenerator):
    """OpenAI-based SQL query generator."""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = OpenAI(api_key=self.settings.OPENAI_API_KEY)
        self.schema_encoder = SchemaEncoder()
        self.security_validator = SQLSecurityValidator()
        self.viz_analyzer = VisualizationAnalyzer()
    
    async def generate_query(
        self,
        query_text: str,
        inspector: Inspector,
        conversation_history: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Generate SQL query using OpenAI's API.
        
        Args:
            query_text: Natural language query
            inspector: SQLAlchemy inspector
            conversation_history: Optional conversation history
            context: Optional additional context
            
        Returns:
            Tuple of (SQL query, visualization metadata)
        """
        try:
            # Encode schema
            schema_text = await self.schema_encoder.encode(inspector)
            
            # Build messages
            messages = self._build_messages(
                query_text,
                schema_text,
                conversation_history,
                context
            )
            
            print(messages)
            
            # Generate SQL
            sql_query = await self._generate_sql(messages)
            
            # Validate
            # await self.validate_query(sql_query)
            
            # Analyze for visualization
            viz_metadata = await self.viz_analyzer.analyze(
                query_text,
                sql_query
            )
            
            return sql_query, viz_metadata
            
        except Exception as e:
            logger.error(f"Query generation failed: {str(e)}", exc_info=True)
            raise QueryGenerationError(f"Failed to generate query: {str(e)}")
    
    async def validate_query(self, query: str) -> bool:
        """
        Validate the generated SQL query.
        
        Args:
            query: SQL query to validate
            
        Returns:
            True if valid, raises exception otherwise
        """
        return await self.security_validator.validate(query)
    
    def _build_messages(
        self,
        query_text: str,
        schema_text: str,
        conversation_history: Optional[List[str]],
        context: Optional[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """Build messages for OpenAI API."""
        messages = [
            {
                "role": "system",
                "content": """You are an expert SQL query generator. Generate:
                - Secure, read-only SQL queries
                - Efficient queries using proper indexing
                - Well-formatted and commented SQL
                - Complex queries using CTEs and window functions when appropriate"""
            }
        ]
        
        if context:
            messages.append({
                "role": "system",
                "content": f"Context:\n{json.dumps(context, indent=2)}"
            })
        
        if conversation_history:
            messages.append({
                "role": "system",
                "content": f"Previous conversation:\n{self._format_history(conversation_history)}"
            })
        
        messages.append({
            "role": "user",
            "content": f"""Schema:
{schema_text}

Query: {query_text}

Generate a SQL query that answers this question."""
        })
        
        return messages
    
    async def _generate_sql(self, messages: List[Dict[str, str]]) -> str:
        """Generate SQL using OpenAI's streaming API."""
        try:
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.settings.OPENAI_MODEL,
                messages=messages,
                temperature=0.1,
                max_tokens=1500,
                response_format={"type": "text"},
                stream=True
            )
            
            sql_parts = []
            # async for chunk in response:
            #     if chunk.choices[0].delta.content:
            #         sql_parts.append(chunk.choices[0].delta.content)
            for chunk in response:
                if chunk.choices[0].delta.content:
                    sql_parts.append(chunk.choices[0].delta.content)
            return "".join(sql_parts)
            
            return "".join(sql_parts)
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}", exc_info=True)
            raise QueryGenerationError(f"OpenAI API error: {str(e)}")
    
    def _format_history(self, history: List[str]) -> str:
        """Format conversation history."""
        return "\n".join(f"- {msg}" for msg in history[-5:])  # Last 5 messages
