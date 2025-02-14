from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import List, Optional
from nlsql.api.middleware import LoggingMiddleware
from nlsql.generators.langchain_generator import LangChainQueryGenerator
import redis.asyncio as redis
import uuid
import json

from ..core.config import get_settings
from ..generators.openai_generator import OpenAIGenerator
from ..utils.database import DatabaseManager
from .schemas import (
    QueryRequest,
    QueryResponse,
    ConversationContext,
    ErrorResponse
)
from .routes import health, query

settings = get_settings()

# Initialize Redis for context management
redis_pool = redis.ConnectionPool.from_url(
    settings.REDIS_URL,
    decode_responses=True
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.redis = redis.Redis(connection_pool=redis_pool)
    app.state.db_manager = DatabaseManager()
    # app.state.generator = OpenAIGenerator()
    app.state.generator = LangChainQueryGenerator()
    
    yield
    
    # Shutdown
    await app.state.redis.close()
    app.state.db_manager.dispose()

app = FastAPI(
    title="Natural Language to SQL API",
    description="API for converting natural language to SQL queries with context management",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with your frontend origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(LoggingMiddleware)


# Include routers
app.include_router(health.router, prefix="/health", tags=["webhook"])
app.include_router(query.router, prefix="/query", tags=["webhook"])
