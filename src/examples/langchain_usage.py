from nlsql.generators.langchain_generator import LangChainQueryGenerator
from nlsql.utils.database import DatabaseManager
from nlsql.schema.encoder import SchemaEncoder
import asyncio
from sqlalchemy import inspect, text
from nlsql.utils.helpers import extract_sql

async def main():
    # Initialize components
    db_manager = DatabaseManager()
    generator = LangChainQueryGenerator()
    
    # Get database inspector and encode schema
    inspector = inspect(db_manager.engine)
    schema_encoder = SchemaEncoder()
    schema_text = await schema_encoder.encode(inspector)
    
    # Example query
    query_text = "List of last 5 customers"
    
    try:
        # Generate SQL query using the LangChain generator.
        generated_text, viz_config = await generator.generate_query(
            query_text=query_text,
            schema=schema_text,
            conversation_history=[]  # No previous context in this example.
        )
        
        # Extract the pure SQL from the generated text
        sql_query = extract_sql(generated_text)
        
        print(f"Generated SQL:\n{sql_query}\n")
        print(f"Visualization Config:\n{viz_config}")
        
        # Execute the generated query.
        with db_manager.get_session() as session:
            result = session.execute(text(sql_query)).fetchall()
            print(f"\nResults:\n{result}")
    
    except Exception as e:
        print(f"Error: {str(e)}")
    
    finally:
        db_manager.dispose()

if __name__ == "__main__":
    asyncio.run(main())
