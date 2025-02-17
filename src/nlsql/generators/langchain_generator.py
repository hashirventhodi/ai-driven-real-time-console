# src/nlsql/generators/langchain_generator.py
from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from typing import Optional, Dict, Any, Tuple, List
from ..core.config import get_settings
from ..core.exceptions import QueryGenerationError
import re
from nlsql.utils.helpers import extract_sql
from nlsql.visualization.analyzer import VisualizationAnalyzer


class LangChainQueryGenerator:
    """LangChain-based SQL query generator that uses conversation context."""
    
    def __init__(self):
        self.settings = get_settings()
        
        # Initialize VisualizationAnalyzer
        self.viz_analyzer = VisualizationAnalyzer()

        self.llm = ChatOpenAI(
            model_name=self.settings.OPENAI_MODEL,
            openai_api_key=self.settings.OPENAI_API_KEY,
            temperature=0.1
        )
        self.prompt_template = PromptTemplate(
            input_variables=["schema", "query_text", "conversation_history"],
            template="""You are an expert SQL query generator.  
Your task is to generate an optimized SQL query based on the given database schema and user query.  

### **Database Schema:**  
{schema}

### **Conversation History:**
{conversation_history}

### **User Query:**
{query_text}

### **Query Rules:**  
1. **Only return a SQL query** (no explanations).  
2. Use `JOINs` where necessary to connect tables properly.  
3. Apply `GROUP BY` for aggregations.  
4. Avoid `DELETE`, `DROP`, `UPDATE`, or modifying data.  
5. Add `LIMIT 10` if the user does not specify limits.  

### **Output Format:**  
Only return the **SQL query** without any additional text.
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
            
            # Extract the pure SQL from the generated text
            sql_query = extract_sql(generated_text)
                        
            # For demonstration, we set a default visualization configuration.
            # viz_config = {
            #     "type": "table",
            #     "settings": {
            #         "pagination": True,
            #         "sortable": True,
            #         "searchable": True
            #     }
            # }
            
            # Analyze for visualization
            viz_metadata = await self.viz_analyzer.analyze(
                query_text,
                sql_query
            )
            
            return sql_query, viz_metadata
        except Exception as e:
            raise QueryGenerationError(f"LangChain generation failed: {str(e)}")