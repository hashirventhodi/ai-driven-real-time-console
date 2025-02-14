from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import json
import uuid
from fastapi import HTTPException
from redis.asyncio import Redis

class ContextManager:
    """Manages conversation contexts using Redis."""
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.context_ttl = timedelta(hours=24)  # Context expires after 24 hours
    
    async def create_context(
        self,
        tenant_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a new conversation context."""
        context_id = str(uuid.uuid4())
        
        context = {
            "context_id": context_id,
            "tenant_id": tenant_id,
            "created_at": datetime.utcnow().isoformat(),
            "last_updated": datetime.utcnow().isoformat(),
            "messages": [],
            "metadata": metadata or {}
        }
        
        # Store in Redis
        key = f"context:{context_id}"
        await self.redis.set(
            key,
            json.dumps(context),
            ex=int(self.context_ttl.total_seconds())
        )
        
        return context_id
    
    async def get_context(self, context_id: str) -> Dict[str, Any]:
        """Retrieve a conversation context."""
        key = f"context:{context_id}"
        context_data = await self.redis.get(key)
        
        if not context_data:
            raise HTTPException(
                status_code=404,
                detail=f"Context {context_id} not found"
            )
        
        return json.loads(context_data)
    
    async def update_context(
        self,
        context_id: str,
        query_text: str,
        sql_query: str,
        results: Dict[str, Any]
    ):
        """Update context with new query and results."""
        context = await self.get_context(context_id)
        
        # Add new message
        context["messages"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "query_text": query_text,
            "sql_query": sql_query,
            "results": results
        })
        
        # Update timestamp
        context["last_updated"] = datetime.utcnow().isoformat()
        
        # Store updated context
        key = f"context:{context_id}"
        await self.redis.set(
            key,
            json.dumps(context),
            ex=int(self.context_ttl.total_seconds())
        )
    
    async def delete_context(self, context_id: str):
        """Delete a conversation context."""
        key = f"context:{context_id}"
        await self.redis.delete(key)
