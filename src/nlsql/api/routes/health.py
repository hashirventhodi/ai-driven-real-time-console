from fastapi import APIRouter, Request, HTTPException
from datetime import datetime

router = APIRouter()

@router.get("/health")
async def health_check(request: Request):
    """
    Check the health of the API and its dependencies.
    """
    try:
        # Check Redis connection
        await request.app.state.redis.ping()
        
        # Check database connection
        with request.app.state.db_manager.get_session() as session:
            session.execute("SELECT 1")
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "dependencies": {
                "redis": "ok",
                "database": "ok"
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Health check failed: {str(e)}"
        )
