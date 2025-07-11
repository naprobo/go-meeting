from sqlalchemy.ext.asyncio import AsyncSession
from models import Log

async def log_action(db: AsyncSession, user_id: int, action: str, detail: str):
    """
    Record a system operation log
    """
    new_log = Log(user_id=user_id, action=action, detail=detail)
    db.add(new_log)
    await db.commit()
