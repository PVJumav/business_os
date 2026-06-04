from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.core.database import get_db

router = APIRouter(
    prefix="/health",
    tags=["Health Check"]
)


@router.get("/database")
def database_health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "success",
            "message": "Database connection is working"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": "Database connection failed",
            "details": str(e)
        }