# server/schemas.py
from pydantic import BaseModel
from typing import Any, Optional

class QueryRequest(BaseModel):
    tenant_id: str
    user_id: Optional[str] = None
    query_text: str

class QueryResponse(BaseModel):
    result: Any
    table_html: Optional[str] = None
    chart_html: Optional[str] = None
