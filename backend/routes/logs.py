from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database import get_db
from models import Log
from routes.auth import get_current_user

router = APIRouter()

@router.get("/api/logs")
async def get_logs(db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    if current_user.group != "Admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    stmt = select(Log).order_by(Log.timestamp.desc())
    logs = await db.execute(stmt)
    logs = logs.scalars().all()

    return [
        {
            "timestamp": log.timestamp,
            "user": log.user_id,
            "action": log.action,
            "detail": log.detail
        } for log in logs
    ]
