from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql.expression import update
from models import Report, Meeting
from database import get_db
from utils.diff_utils import compute_diff
from routes.auth import get_current_user
from sqlalchemy.orm import joinedload
from pydantic import BaseModel

class ReportCreate(BaseModel):
    content: str

router = APIRouter()

@router.get("/api/meetings/{meeting_id}/reports")
async def get_reports(
    meeting_id: int, 
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Login required")
    """
    Get all progress reports for the meeting.
    """
    stmt = (
        select(Report)
        .where(Report.meeting_id == meeting_id)
        .options(joinedload(Report.user))
        .order_by(Report.id.asc())
    )

    result = await db.execute(stmt)
    reports = result.scalars().all()

    results = []
    for report in reports:
        results.append({
            "id": report.id,
            "user_id": report.user_id,
            "user": {
                "username": report.user.username if report.user else "Unknown User",
                "fullname": report.user.fullname if report.user and report.user.fullname else report.user.username
            },
            "content": report.content
        })

    return results

@router.get("/api/meetings/{meeting_id}/reports/user/{user_id}")
async def get_user_report(
    meeting_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Login required")
    """
    Get a user's progress reports in the specified meeting.
    """
    stmt = (
        select(Report)
        .where(Report.meeting_id == meeting_id)
        .where(Report.user_id == user_id)
        .options(joinedload(Report.user))
    )

    result = await db.execute(stmt)
    reports = result.scalars().all()

    if not reports:
        raise HTTPException(status_code=404, detail="Report not found")

    user_info = {
        "user_id": user_id,
        "fullname": reports[0].user.fullname if reports[0].user else None,
        "username": reports[0].user.username if reports[0].user else None
    }

    return {
        "user": user_info,
        "reports": [{"id": r.id, "content": r.content} for r in reports]
    }

@router.post("/api/meetings/{meeting_id}/newreport")
async def submit_report(
    meeting_id: int,
    report: ReportCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Login required")

    # Check permissions
    if current_user.group not in ["Leader", "Admin"]:
        raise HTTPException(status_code=403, detail="Permission denied")

    # Check for existing report
    stmt = select(Report).where(
        Report.user_id == current_user.id,
        Report.meeting_id == meeting_id
    )
    result = await db.execute(stmt)
    existing_report = result.scalar_one_or_none()

    # Update or insert
    if existing_report:
        stmt = (
            update(Report)
            .where(Report.user_id == current_user.id, Report.meeting_id == meeting_id)
            .values(content=report.content)
            .execution_options(synchronize_session=False)
        )
        await db.execute(stmt)
    else:
        new_report = Report(
            user_id=current_user.id,
            meeting_id=meeting_id,
            content=report.content
        )
        db.add(new_report)

    await db.commit()
    return {"message": "Progress report submitted"}

@router.put("/api/meetings/{meeting_id}/reports/{report_id}")
async def update_report(
    meeting_id: int,
    report_id: int,
    report: ReportCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Login required")

    stmt = select(Report).where(Report.id == report_id, Report.meeting_id == meeting_id, Report.user_id == current_user.id)
    result = await db.execute(stmt)
    existing_report = result.scalar_one_or_none()

    if not existing_report:
        raise HTTPException(status_code=404, detail="Report not found")

    existing_report.content = report.content
    await db.commit()

    return {"message": "Progress report updated"}

@router.get("/api/reports/last/{user_id}")
async def get_last_report(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Get the user's most recent report across all meetings
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Login required")

    stmt = (
        select(Report)
        .where(Report.user_id == user_id)
        .order_by(Report.id.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(status_code=404, detail="No past report found")

    return {"report": {"content": report.content, "meeting_id": report.meeting_id, "created_at": "N/A (ID-based)"}}

@router.get("/api/reports/previous/{meeting_id}/{user_id}")
async def get_previous_report_before_meeting(
    meeting_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Get the latest report submitted by a user before the specified meeting
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Login required")

    # Get current meeting date
    stmt_meeting = select(Meeting).where(Meeting.id == meeting_id)
    meeting_result = await db.execute(stmt_meeting)
    current_meeting = meeting_result.scalar_one_or_none()

    if not current_meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    # Find user's latest report before the meeting
    stmt = (
        select(Report)
        .join(Meeting, Report.meeting_id == Meeting.id)
        .where(Report.user_id == user_id)
        .where(Meeting.date < current_meeting.date)
        .order_by(Meeting.date.desc())
        .limit(1)
    )

    result = await db.execute(stmt)
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(status_code=404, detail="No previous report found")

    return {
        "report": {
            "content": report.content,
            "meeting_id": report.meeting_id,
            "created_at": str(report.created_at) if hasattr(report, "created_at") else "N/A",
        }
    }
