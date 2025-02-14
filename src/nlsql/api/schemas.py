from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class QueryRequest(BaseModel):
    query_text: str = Field(..., description="Natural language query")
    context_id: Optional[str] = Field(None, description="Conversation context ID")
    tenant_id: str = Field(..., description="Tenant identifier")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")

class QueryResponse(BaseModel):
    sql_query: str = Field(..., description="Generated SQL query")
    results: List[Dict[str, Any]] = Field(..., description="Query results")
    visualization: Dict[str, Any] = Field(..., description="Visualization configuration")
    context_id: str = Field(..., description="Conversation context ID")

class ConversationContext(BaseModel):
    context_id: str = Field(..., description="Unique context identifier")
    tenant_id: str = Field(..., description="Tenant identifier")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
