# src/nlsql/generators/langchain_generator.py
from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from typing import Optional, Dict, Any, Tuple, List
from ..core.config import get_settings
from ..core.exceptions import QueryGenerationError
import re

class LangChainQueryGenerator:
    """LangChain-based SQL query generator that uses conversation context."""
    
    def __init__(self):
        self.settings = get_settings()

        self.llm = ChatOpenAI(
            model_name=self.settings.OPENAI_MODEL,
            openai_api_key=self.settings.OPENAI_API_KEY,
            temperature=0.1
        )
        self.prompt_template = PromptTemplate(
            input_variables=["schema", "query_text", "conversation_history"],
            template="""You are an expert SQL query generator.
Given the following database schema:
{schema}

Conversation history:
{conversation_history}

Current natural language query:
{query_text}

Generate only the SQL query without any additional explanation.
"""
        )
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt_template)
    
    async def generate_query(
        self, 
        query_text: str, 
        schema: str, 
        conversation_history: Optional[List[str]] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """Generate SQL query using LangChain and return a visualization config."""
        history_str = "\n".join(conversation_history) if conversation_history else "None"
        try:
            generated_text = await self.chain.arun(
                schema=schema,
                query_text=query_text,
                conversation_history=history_str
            )
            print(f"Generated Text:\n{generated_text}\n")
                        
            # For demonstration, we set a default visualization configuration.
            viz_config = {
                "type": "table",
                "settings": {
                    "pagination": True,
                    "sortable": True,
                    "searchable": True
                }
            }
            return generated_text, viz_config
        except Exception as e:
            raise QueryGenerationError(f"LangChain generation failed: {str(e)}")