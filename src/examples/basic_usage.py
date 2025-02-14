from nlsql.generators.openai_generator import OpenAIGenerator
from nlsql.utils.database import DatabaseManager
import asyncio
from sqlalchemy import inspect

async def main():
    # Initialize components
    db_manager = DatabaseManager()
    generator = OpenAIGenerator()
    
    # Get database inspector
    # inspector = db_manager.engine.inspector
    inspector = inspect(db_manager.engine)
    
    # Example query
    query_text = "List of last 5 customers"
    
    try:
        # Generate SQL query
        sql_query, viz_config = await generator.generate_query(
            query_text=query_text,
            inspector=inspector
        )
        
        print(f"Generated SQL:\n{sql_query}\n")
        print(f"Visualization Config:\n{viz_config}")
        
        # Execute query
        with db_manager.get_session() as session:
            result = session.execute(sql_query).fetchall()
            print(f"\nResults:\n{result}")
    
    except Exception as e:
        print(f"Error: {str(e)}")
    
    finally:
        db_manager.dispose()

if __name__ == "__main__":
    asyncio.run(main())