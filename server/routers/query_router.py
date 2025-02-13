# server/routers/query_router.py

from sqlalchemy import inspect  # Import the correct utility function
from fastapi import APIRouter, HTTPException
from server.schemas import QueryRequest, QueryResponse
from server.multi_tenancy import get_tenant_session
from conversation.conversation_manager import add_message_to_history, get_conversation_history
from nlp.query_understanding import process_natural_language_query
from server.utils.response_utils import to_table, generate_chart
from sqlalchemy.exc import SQLAlchemyError
from typing import Dict, Any

router = APIRouter()

@router.post("/query", response_model=QueryResponse)
def handle_query(payload: QueryRequest) -> Dict[str, Any]:
    """
    Accepts a user query, uses LLM to generate SQL, executes on that tenant's DB, 
    returns results as JSON with optional chart HTML or table HTML.
    """
    tenant_id = payload.tenant_id
    user_id = payload.user_id or "anonymous"
    user_query = payload.query_text
    
    print("AAA 111")

    # 1. Get DB session for tenant
    try:
        db_session = get_tenant_session(tenant_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    print("AAA 222")
    # 2. Add user query to conversation history (Redis)
    add_message_to_history(user_id, f"User Query: {user_query}")
    
    print("AAA 333")

    # 3. Fetch recent conversation 
    history = get_conversation_history(user_id, limit=10)
    print("AAA 444")

    # 4. Reflect & Summarize schema -> Generate SQL
    try:
        print("AAA 444 - A")
        
        # inspector = inspect(db_session.get_bind())  # Use `sqlalchemy.inspect`
        # inspector = db_session.get_bind().inspect(db_session.get_bind())
        inspector = inspect(db_session.get_bind())
        # for table_name in inspector.get_table_names():
        #     columns = inspector.get_columns(table_name)
        #     print(f"Table {table_name} has columns: {columns}")

        
        print("AAA 444 - B")

        generated_sql, chart_info = process_natural_language_query(
            query_text=user_query,
            db=db_session,
            metadata=inspector,
            conversation_history=history,
            use_openai=True  # set to True if you want OpenAI
        )
    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail=f"Error generating SQL: {str(e)}")

    print("AAA 555")
    print("Generated SQL Query:", generated_sql)
    
    print("AAA 555 - END")

    # 5. Execute SQL
    try:
        result = db_session.execute(generated_sql).fetchall()
    except SQLAlchemyError as e:
        print(e)
        raise HTTPException(status_code=400, detail=f"SQL Execution Error: {str(e)}")

    print("AAA 666")
    
    columns = result[0].keys() if result else []
    data = [dict(zip(columns, row)) for row in result]

    # 6. Build response
    resp_data = {"result": data}

    if chart_info and data:
        import pandas as pd
        df = pd.DataFrame(data)
        resp_data["chart_html"] = generate_chart(chart_info["type"], df, chart_info["x"], chart_info["y"])
    else:
        resp_data["table_html"] = to_table(data)

    # 7. Add system response to conversation
    add_message_to_history(user_id, f"System Response: {resp_data}")
    return resp_data
