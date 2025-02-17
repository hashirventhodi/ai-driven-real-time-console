from nlsql.generators.openai_generator import OpenAIGenerator
from nlsql.utils.database import DatabaseManager
from nlsql.visualization.analyzer import VisualizationAnalyzer
import asyncio
import json

async def main():
    # Initialize components
    db_manager = DatabaseManager()
    generator = OpenAIGenerator()
    viz_analyzer = VisualizationAnalyzer()
    
    # Get database inspector
    inspector = db_manager.engine.inspector
    
    # Example complex query with context
    query_text = "Compare monthly orders"
    context = {
        "time_period": "2023",
        "metrics": ["sales", "revenue"],
        "dimensions": ["region", "month"]
    }
    
    # Example conversation history
    conversation_history = [
        "Show me total sales for 2023",
        "Break it down by region",
        "Which region had the highest growth?"
    ]
    
    try:
        # Generate SQL query with context
        sql_query, viz_config = await generator.generate_query(
            query_text=query_text,
            inspector=inspector,
            
            conversation_history=conversation_history,
            context=context
        )
        
        print(f"Generated SQL:\n{sql_query}\n")
        print(f"Visualization Config:\n{json.dumps(viz_config, indent=2)}")
        
        # Execute query
        with db_manager.get_session() as session:
            result = session.execute(sql_query).fetchall()
            
            # Convert results to list of dicts
            columns = result[0].keys()
            data = [dict(zip(columns, row)) for row in result]
            
            print(f"\nResults:\n{json.dumps(data, indent=2)}")
    
    except Exception as e:
        print(f"Error: {str(e)}")
    
    finally:
        db_manager.dispose()

if __name__ == "__main__":
    asyncio.run(main())