from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from database import get_db
from models import Meeting, User, MeetingMinutes
from routes.auth import get_current_user
from utils.log_utils import log_action
from utils.email_utils import send_email
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from utils.mattermost_notifier import send_message
import json

class MeetingCreate(BaseModel):
    title: str
    date: datetime
    facilitator_id: int
    recorder_id: int
    online_meeting_url: Optional[str] = None  # Optional field

class MeetingUpdate(BaseModel):
    title: Optional[str] = None
    date: Optional[datetime] = None
    facilitator_id: Optional[int] = None
    recorder_id: Optional[int] = None
    online_meeting_url: Optional[str] = None

router = APIRouter()

@router.post("/meetings")
async def create_meeting(
    meeting: MeetingCreate, 
    db: AsyncSession = Depends(get_db), 
    current_user=Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Login required")
        
    # Only Admin or Leader can create meetings
    if current_user.group not in ["Admin", "Leader"]:
        raise HTTPException(status_code=403, detail="Permission denied")

    # Ensure facilitator and recorder exist
    facilitator = await db.execute(select(User).where(User.id == meeting.facilitator_id))
    facilitator = facilitator.scalar_one_or_none()
    if not facilitator:
        raise HTTPException(status_code=400, detail="Facilitator not found")

    recorder = await db.execute(select(User).where(User.id == meeting.recorder_id))
    recorder = recorder.scalar_one_or_none()
    if not recorder:
        raise HTTPException(status_code=400, detail="Recorder not found")

    # Create meeting
    new_meeting = Meeting(
        title=meeting.title,
        date=meeting.date,
        facilitator_id=meeting.facilitator_id,
        recorder_id=meeting.recorder_id,
        online_meeting_url=meeting.online_meeting_url,
        status="Not Started"
    )

    db.add(new_meeting)
    await db.commit()
    await db.refresh(new_meeting)  # Ensure ID is returned to frontend

    return {"message": "Meeting created", "meeting_id": new_meeting.id}

@router.put("/meetings/{meeting_id}")
async def update_meeting(
    meeting_id: int,
    meeting_update: MeetingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Login required")

    if current_user.group not in ["Admin", "Leader"]:
        raise HTTPException(status_code=403, detail="Permission denied")

    meeting = await db.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    # Update only provided fields
    if meeting_update.title is not None:
        meeting.title = meeting_update.title
    if meeting_update.date is not None:
        meeting.date = meeting_update.date
    if meeting_update.facilitator_id is not None:
        facilitator = await db.get(User, meeting_update.facilitator_id)
        if not facilitator:
            raise HTTPException(status_code=400, detail="Facilitator not found")
        meeting.facilitator_id = meeting_update.facilitator_id
    if meeting_update.recorder_id is not None:
        recorder = await db.get(User, meeting_update.recorder_id)
        if not recorder:
            raise HTTPException(status_code=400, detail="Recorder not found")
        meeting.recorder_id = meeting_update.recorder_id
    if meeting_update.online_meeting_url is not None:
        meeting.online_meeting_url = meeting_update.online_meeting_url

    await db.commit()
    await db.refresh(meeting)

    return {"message": "Meeting updated", "meeting_id": meeting.id}

@router.get("/meetings")
async def get_meetings(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Login required")

    result = await db.execute(select(Meeting))
    meetings = result.scalars().all()

    meeting_list = []
    for meeting in meetings:
        facilitator = await db.get(User, meeting.facilitator_id)
        recorder = await db.get(User, meeting.recorder_id)

        meeting_list.append({
            "id": meeting.id,
            "title": meeting.title,
            "date": meeting.date,
            "status": meeting.status,
            "facilitator": facilitator.fullname if facilitator else "Undecided",
            "recorder": recorder.fullname if recorder else "Undecided",
            "online_meeting_url": meeting.online_meeting_url
        })

    return meeting_list

@router.get("/meetings/{meeting_id}")
async def get_meeting(
    meeting_id: int, 
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Login required")

    stmt = select(Meeting).where(Meeting.id == meeting_id)
    result = await db.execute(stmt)
    meeting = result.scalar_one_or_none()
    
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    facilitator = await db.get(User, meeting.facilitator_id)
    recorder = await db.get(User, meeting.recorder_id)

    return {
        "id": meeting.id,
        "title": meeting.title,
        "date": meeting.date,
        "status": meeting.status,
        "facilitator": facilitator.fullname if facilitator else "Undecided",
        "facilitator_id": meeting.facilitator_id,
        "recorder": recorder.fullname if recorder else "Undecided",
        "recorder_id": meeting.recorder_id,
        "online_meeting_url": meeting.online_meeting_url
    }

@router.get("/meetings/{meeting_id}/participants")
async def get_meeting_participants(
    meeting_id: int, 
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Login required")

    stmt = select(MeetingParticipants).where(MeetingParticipants.meeting_id == meeting_id)
    result = await db.execute(stmt)
    participants = result.scalars().all()

    return [
        {"user_id": p.user_id, "username": p.user.username, "role": p.role}
        for p in participants
    ]

@router.post("/meetings/{meeting_id}/end")
async def end_meeting(
    meeting_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Login required")

    meeting = await db.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    if meeting.facilitator_id != current_user.id:
        raise HTTPException(status_code=403, detail="You don't have permission to end this meeting")

    if meeting.status != "In Progress":
        raise HTTPException(status_code=400, detail="Meeting has already ended")

    meeting.status = "Ended"
    await db.commit()
    return {"status": meeting.status, "message": "Meeting has ended"}

@router.delete("/meetings/{meeting_id}")
async def delete_meeting(
    meeting_id: int, 
    db: AsyncSession = Depends(get_db), 
    current_user = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Login required")

    if current_user.group != "Admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    stmt = select(Meeting).where(Meeting.id == meeting_id)
    meeting = await db.execute(stmt)
    meeting = meeting.scalar_one_or_none()

    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    await db.delete(meeting)
    await db.commit()
    return {"message": "Meeting deleted"}

@router.post("/meetings/{meeting_id}/start")
async def start_meeting(
    meeting_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Login required")

    result = await db.execute(select(Meeting).where(Meeting.id == meeting_id))
    meeting = result.scalar_one_or_none()

    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    if meeting.facilitator_id != current_user.id:
        raise HTTPException(status_code=403, detail="You don't have permission to start this meeting")

    meeting.status = "In Progress"
    await db.commit()

    return {"message": "Meeting started", "status": meeting.status}

class MeetingMinutesSchema(BaseModel):
    content: dict  # Meeting minutes content (JSON format)
    is_approved: bool = True  # Whether the minutes are approved

@router.get("/meetings/{meeting_id}/minutes")
async def get_meeting_minutes(
    meeting_id: int, 
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Login required")

    result = await db.execute(
        select(MeetingMinutes)
        .where(MeetingMinutes.meeting_id == meeting_id)
        .options(joinedload(MeetingMinutes.recorder))
    )
    minutes = result.scalar_one_or_none()

    if not minutes:
        raise HTTPException(status_code=404, detail="Minutes not found")

    return {
        "id": minutes.id,
        "meeting_id": minutes.meeting_id,
        "recorder_id": minutes.recorder_id,
        "recorder_name": minutes.recorder.fullname if minutes.recorder else "Unknown",
        "content": minutes.content,
        "is_approved": minutes.is_approved,
        "created_at": minutes.created_at,
        "updated_at": minutes.updated_at
    }

@router.post("/meetings/{meeting_id}/minutes")
async def save_meeting_minutes(
    meeting_id: int,
    minutes_data: MeetingMinutesSchema,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Login required")
    try:
        meeting = await db.get(Meeting, meeting_id)
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")

        result = await db.execute(select(MeetingMinutes).where(MeetingMinutes.meeting_id == meeting_id))
        minutes = result.scalar_one_or_none()

        if minutes:
            if minutes.recorder_id != current_user.id:
                raise HTTPException(status_code=403, detail="Permission denied")
            minutes.content = json.dumps(minutes_data.content)
            minutes.is_approved = minutes_data.is_approved
            minutes.updated_at = datetime.utcnow()
        else:
            minutes = MeetingMinutes(
                meeting_id=meeting_id,
                recorder_id=current_user.id,
                content=json.dumps(minutes_data.content),
                is_approved=minutes_data.is_approved
            )
            db.add(minutes)

        await db.commit()

        await send_email(
            to_email='xxxxxx@xxxxxxxxxx.com',
            subject='[Notice] New meeting minutes have been saved',
            html_content='<p>New meeting minutes have been saved.</p>'
        )
        
        meeting_title = meeting.title or f"ID:{meeting_id}"
        meeting_date = meeting.date.strftime("%-m/%-d") if meeting.date else ""
        meeting_url = f"https://gomeeting.xxx.yyy/#/meeting/{meeting.id}"
        notice_text = (
            f"@all\n"
            f"{meeting_date}　**{meeting_title}**　[Minutes]({meeting_url}) have been created. (By: {current_user.fullname})"
        )
        send_message("mattermost-channel-id", notice_text)

        return {"message": "Minutes saved"}
    
    except Exception as e:
        print(f"Error saving: {str(e)}")
        raise HTTPException(status_code=500, detail="Server error")
