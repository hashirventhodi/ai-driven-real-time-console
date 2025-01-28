# server/main.py
import uvicorn
from fastapi import FastAPI
from server.routers.query_router import router as query_router

app = FastAPI(title="Conversational AI w/ Summarized Schema")

app.include_router(query_router, prefix="/api", tags=["query"])

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
