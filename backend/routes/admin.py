from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database import get_db
from models import User
from routes.auth import get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/api/admin", tags=["Admin"])

# Unified user update request model
class UserUpdate(BaseModel):
    is_approved: bool = None
    is_active: bool = None
    new_group: str = None  # Used to change user group

# Retrieve all user information (excluding password_hash)
@router.get("/users")
async def get_users(db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.group != "Admin":
        raise HTTPException(status_code=403, detail="Permission denied")
    
    result = await db.execute(select(User))
    users = result.scalars().all()

    return [
        {
            "id": user.id,
            "username": user.username,
            "fullname": user.fullname,
            "group": user.group,
            "is_approved": user.is_approved,
            "is_active": user.is_active
        }
        for user in users
    ]

# User approval
class ApproveUserRequest(BaseModel):
    is_approved: bool  # Parse JSON request body

@router.put("/users/{user_id}/approve")
async def approve_user(user_id: int, request: ApproveUserRequest, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.group != "Admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_approved = request.is_approved
    await db.commit()
    status = "approved" if request.is_approved else "unapproved"
    return {"message": f"User {user.username} status has been updated to {status}"}

# Enable/disable user
class DisableUserRequest(BaseModel):
    is_active: bool  # Parse JSON request body

@router.put("/users/{user_id}/disable")
async def disable_user(user_id: int, request: DisableUserRequest, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.group != "Admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = request.is_active
    await db.commit()
    action = "activated" if request.is_active else "deactivated"
    return {"message": f"User {user.username} has been {action}"}

# Change user group
class UserGroupUpdate(BaseModel):
    new_group: str  # Parse JSON request body

@router.put("/users/{user_id}/group")
async def change_user_group(user_id: int, request: UserGroupUpdate, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.group != "Admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    allowed_groups = ["Member", "Leader", "Admin", "Manager"]
    if request.new_group not in allowed_groups:
        raise HTTPException(status_code=400, detail="Invalid group name")

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.group = request.new_group
    await db.commit()
    return {"message": f"User {user.username}'s group has been changed to {request.new_group}"}

@router.delete("/users/{user_id}")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.group != "Admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db.delete(user)
    await db.commit()
    return {"message": f"User {user.username} has been deleted"}
