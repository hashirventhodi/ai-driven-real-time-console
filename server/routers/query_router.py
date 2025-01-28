# server/routers/query_router.py
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

    # 1. Get DB session for tenant
    try:
        db_session = get_tenant_session(tenant_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 2. Add user query to conversation history (Redis)
    add_message_to_history(user_id, f"User Query: {user_query}")

    # 3. Fetch recent conversation 
    history = get_conversation_history(user_id, limit=10)

    # 4. Reflect & Summarize schema -> Generate SQL
    try:
        inspector = db_session.get_bind().inspect(db_session.get_bind())
        generated_sql, chart_info = process_natural_language_query(
            query_text=user_query,
            db=db_session,
            metadata=inspector,
            conversation_history=history,
            use_openai=False  # set to True if you want OpenAI
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error generating SQL: {str(e)}")

    # 5. Execute SQL
    try:
        result = db_session.execute(generated_sql).fetchall()
    except SQLAlchemyError as e:
        raise HTTPException(status_code=400, detail=f"SQL Execution Error: {str(e)}")

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
