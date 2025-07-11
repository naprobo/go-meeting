from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from sqlalchemy.future import select
from database import get_db
from models import User
import bcrypt, jwt, os
from pydantic import BaseModel

class LoginRequest(BaseModel):
    username: str
    password: str

class UserCreate(BaseModel):
    username: str
    fullname: str  # New field
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    group: str
    is_approved: bool  # Ensure to return approval status

SECRET_KEY = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
ALGORITHM = "HS256"

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")

        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=401, detail="Invalid user")

        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    meeting_id: int = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user info. If `meeting_id` is provided, also return the user's role in that meeting.
    """
    user_info = {
        "id": current_user.id,
        "username": current_user.username,
        "fullname": current_user.fullname,
        "group": current_user.group,  # Fixed identity
        "is_approved": current_user.is_approved,
        "role": None  # Default no role
    }

    # If meeting_id is provided, query the user's role
    if meeting_id:
        stmt = select(MeetingParticipants).where(
            MeetingParticipants.meeting_id == meeting_id,
            MeetingParticipants.user_id == current_user.id
        )
        result = await db.execute(stmt)
        participant = result.scalar_one_or_none()
        if participant:
            user_info["role"] = participant.role

    return user_info

async def get_user_by_username(db: AsyncSession, username: str):
    query = text("SELECT * FROM users WHERE username = :username")
    result = await db.execute(query, {"username": username})
    return result.fetchone()

@router.post("/register", response_model=UserOut)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    User registration
    """
    existing_user = await db.execute(select(User).where(User.username == user.username))
    if existing_user.scalars().first():  # Changed to `.scalars().first()`
        raise HTTPException(status_code=400, detail="Username is already taken")

    hashed_password = bcrypt.hashpw(user.password.encode("utf-8"), bcrypt.gensalt()).decode()  # Fix encoding issue

    new_user = User(
        username=user.username,
        fullname=user.fullname,
        password_hash=hashed_password,  # Store hashed password
        group="user",
        is_active=True,
        is_approved=False,
    )

    db.add(new_user)
    await db.commit()
    return new_user

@router.post("/login")
async def login(user: LoginRequest, db: AsyncSession = Depends(get_db)):
    db_user = await get_user_by_username(db, user.username)
    if not db_user or not bcrypt.checkpw(user.password.encode(), db_user.password_hash.encode()):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    if not db_user.is_approved:
        raise HTTPException(status_code=403, detail="Your account is pending approval")

    if not db_user.is_active:
        raise HTTPException(status_code=403, detail="Your account is not active")

    token = jwt.encode({"user_id": db_user.id, "fullname": db_user.fullname, "group": db_user.group}, SECRET_KEY, algorithm="HS256")
    return {"token": token, "user": {"id": db_user.id, "username": db_user.username, "fullname": db_user.fullname, "group": db_user.group}}

@router.post("/logout")
async def logout():
    """
    Instruct frontend to delete token
    """
    return {"message": "Logged out successfully"}
