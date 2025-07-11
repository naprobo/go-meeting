from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, DateTime, func, Float
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    fullname = Column(String, nullable=True)  # Real name
    password_hash = Column(String, nullable=False)
    group = Column(String, nullable=False)  # "Admin", "Leader", "Member"
    is_active = Column(Boolean, default=True)
    is_approved = Column(Boolean, default=False)  # Whether approved by admin

    reports = relationship("Report", back_populates="user")  # Related reports
    comments = relationship("ReportComment", back_populates="user", cascade="all, delete-orphan")  # Related comments

class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    date = Column(DateTime, nullable=False)
    status = Column(String, default="Not Started")
    facilitator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recorder_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    online_meeting_url = Column(String, nullable=True)

    facilitator = relationship("User", foreign_keys=[facilitator_id])
    recorder = relationship("User", foreign_keys=[recorder_id])

    participants = relationship("MeetingParticipants", back_populates="meeting", cascade="all, delete-orphan")
    minutes = relationship("MeetingMinutes", uselist=False, back_populates="meeting", cascade="all, delete-orphan")
    comments = relationship("ReportComment", back_populates="meeting", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="meeting", cascade="all, delete-orphan")

class MeetingMinutes(Base):
    __tablename__ = "meeting_minutes"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False, unique=True)  # Only one record per meeting
    recorder_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Recorder
    content = Column(Text, nullable=False)  # Meeting content
    is_approved = Column(Boolean, default=False)  # Whether approved
    created_at = Column(DateTime, default=func.now())  # Created timestamp
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())  # Last updated timestamp

    meeting = relationship("Meeting", back_populates="minutes")
    recorder = relationship("User")

class MeetingParticipants(Base):
    __tablename__ = "meeting_participants"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    user = relationship("User")
    meeting = relationship("Meeting")

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False)  # Related meeting
    content = Column(Text, nullable=False)  # Report content in JSON format

    user = relationship("User", back_populates="reports", lazy="joined")
    meeting = relationship("Meeting", back_populates="reports", lazy="joined")
    comments = relationship("ReportComment", back_populates="report", cascade="all, delete-orphan")  # Related comments

class ReportComment(Base):
    __tablename__ = "report_comments"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id"), nullable=False)  # Related report
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Commenter
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False)  # Belongs to meeting (for quick lookup)
    content = Column(Text, nullable=False)  # Comment content
    created_at = Column(DateTime, default=func.now())  # Created timestamp

    user = relationship("User", back_populates="comments")
    report = relationship("Report", back_populates="comments")
    meeting = relationship("Meeting", back_populates="comments")

class Log(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String, nullable=False)  # e.g., "Create Meeting", "Submit Report", "End Meeting"
    detail = Column(String, nullable=False)  # Detail description
    timestamp = Column(DateTime, default=func.now())  # Operation time

class DeliverySummary(Base):
    __tablename__ = "delivery_summaries"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)  # e.g., "June 2025 Delivery"
    month = Column(String, nullable=False)  # e.g., "2025-06"
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=func.now())

    creator = relationship("User")
    deliveries = relationship("DeliveryDetail", back_populates="summary", cascade="all, delete-orphan")

class DeliveryDetail(Base):
    __tablename__ = "delivery_details"

    id = Column(Integer, primary_key=True, index=True)
    summary_id = Column(Integer, ForeignKey("delivery_summaries.id"), nullable=False)
    project_name = Column(String(100), nullable=False)
    contract_number = Column(String(50), nullable=True)
    delivery_date = Column(DateTime, nullable=False)
    delivery_status = Column(String(20), nullable=False)  # 'Planned', 'Delivered', 'Delayed'
    contract_start = Column(DateTime, nullable=True)
    contract_end = Column(DateTime, nullable=True)
    delivery_person_name = Column(String(100), nullable=True)  # Free text, not limited to system users
    overtime_cost_request = Column(String, nullable=True)  # e.g., "Request Addition", "Deduction"
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    base_hours_min = Column(Float, nullable=True, default=140.0)   # Deduct if below this
    base_hours_std = Column(Float, nullable=True, default=160.0)   # Standard work hours
    base_hours_max = Column(Float, nullable=True, default=180.0)   # Add if above this

    summary = relationship("DeliverySummary", back_populates="deliveries")
    creator = relationship("User")
    members = relationship("DeliveryMember", back_populates="delivery", cascade="all, delete-orphan")

class DeliveryMember(Base):
    __tablename__ = "delivery_members"

    id = Column(Integer, primary_key=True, index=True)
    delivery_id = Column(Integer, ForeignKey("delivery_details.id"), nullable=False)
    member_name = Column(String(100), nullable=False)
    work_ratio = Column(Float, nullable=False, default=1.0)  # e.g., 1.0, 0.5, 1.5
    unit_price = Column(Integer, nullable=False)
    monthly_hours = Column(Float, nullable=True)  # Total hours in the month, to two decimal places

    delivery = relationship("DeliveryDetail", back_populates="members")
