from nlsql.generators.openai_generator import OpenAIGenerator
from nlsql.utils.database import DatabaseManager
import asyncio
from sqlalchemy import inspect
from nlsql.schema.encoder import SchemaEncoder

async def main():
    # Initialize components
    db_manager = DatabaseManager()
    generator = OpenAIGenerator()
    
    # Get database inspector
    # inspector = db_manager.engine.inspector
    inspector = inspect(db_manager.engine)
    schema_encoder = SchemaEncoder()
    schema_text = await schema_encoder.encode(inspector)
    
    
    
    try:
        
       print("Generated Schema:", schema_text)
        
    
    
    except Exception as e:
        print(f"Error: {str(e)}")
        
    finally:
        db_manager.dispose()

if __name__ == "__main__":
    asyncio.run(main())