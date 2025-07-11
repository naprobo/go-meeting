from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import User
from database import get_db

router = APIRouter()

@router.get("/api/users")
async def get_users(db: AsyncSession = Depends(get_db)):
    """
    Retrieve a list of all users
    """
    stmt = select(User.id, User.fullname, User.group)
    result = await db.execute(stmt)
    users = result.all()

    if not users:
        raise HTTPException(status_code=404, detail="Users not found")

    return [{"id": u.id, "username": u.fullname, "group": u.group} for u in users]
