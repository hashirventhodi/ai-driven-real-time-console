from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Any, Dict, Optional

from nlsql.schema.encoder import SchemaEncoder
from ..schemas import QueryRequest, QueryResponse, ErrorResponse
from ..context import ContextManager
from sqlalchemy import inspect, text
from nlsql.utils.helpers import extract_sql
import orjson
from datetime import date, datetime

router = APIRouter()

from decimal import Decimal


def custom_json_serializer(obj: Any) -> Any:
    """Custom JSON serializer to handle Decimal types."""
    if isinstance(obj, Decimal):
        return float(obj)
    return str(obj)


@router.post(
    "/query",
    response_model=QueryResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
async def process_query(
    request: Request,
    query_req: QueryRequest,
):
    """
    Process a natural language query and return SQL results.
    """
    try:
        # Get services from app state
        context_manager = ContextManager(request.app.state.redis)
        generator = request.app.state.generator
        db_manager = request.app.state.db_manager
        
        # Get or create context
        context_id = query_req.context_id
        if not context_id:
            context_id = await context_manager.create_context(
                query_req.tenant_id,
                query_req.metadata
            )
        
        # Get context and conversation history
        context = await context_manager.get_context(context_id)
        conversation_history = [
            msg["query_text"] for msg in context["messages"][-5:]
        ]
        
        # Generate SQL
        inspector = inspect(db_manager.engine)
        schema_encoder = SchemaEncoder()
        schema_text = await schema_encoder.encode(inspector)
        
        # Generate the SQL query using the LangChain generator
        sql_query, viz_config = await generator.generate_query(
            query_text=query_req.query_text,
            schema=schema_text,
            conversation_history=conversation_history
        )
        
        # Execute query
        with db_manager.get_session() as session:
            result = session.execute(text(sql_query))
            columns = result.keys()  # Get column names
            rows = result.fetchall()  # Fetch all rows
            
            # Convert rows to dictionaries with proper decimal and date handling
        data = []
        for row in rows:
            row_dict = {}
            for col, value in zip(columns, row):
                if isinstance(value, Decimal):
                    row_dict[col] = float(value)  # Convert Decimal to float
                elif isinstance(value, (date, datetime)):
                    row_dict[col] = value.isoformat()  # Convert date/datetime to ISO format
                else:
                    row_dict[col] = value
            data.append(row_dict)
        
        # Update context
        await context_manager.update_context(
            context_id,
            query_req.query_text,
            sql_query,
            data
        )
        
        # Return using the Pydantic model
        return QueryResponse(
            sql_query=sql_query,
            results=data,
            visualization=viz_config,
            context_id=context_id
        )
        
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/context/{context_id}",
    response_model=Dict[str, Any],
    responses={404: {"model": ErrorResponse}}
)
async def get_conversation_context(
    request: Request,
    context_id: str,
):
    """
    Retrieve a conversation context.
    """
    context_manager = ContextManager(request.app.state.redis)
    return await context_manager.get_context(context_id)

@router.delete(
    "/context/{context_id}",
    status_code=204
)
async def delete_conversation_context(
    request: Request,
    context_id: str,
):
    """
    Delete a conversation context.
    """
    context_manager = ContextManager(request.app.state.redis)
    await context_manager.delete_context(context_id)
