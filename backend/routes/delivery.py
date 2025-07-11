from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from typing import List
from datetime import datetime
from models import DeliverySummary, DeliveryDetail, DeliveryMember
from database import get_db
from routes.auth import get_current_user

router = APIRouter()

# ------------------ Pydantic Models ------------------

class DeliveryMemberSchema(BaseModel):
    member_name: str
    unit_price: int
    total_hours: float | None = None
    work_ratio: float = 1.0

class DeliveryDetailSchema(BaseModel):
    project_name: str
    contract_number: str | None = None
    delivery_date: str
    delivery_status: str
    contract_start: str | None = None
    contract_end: str | None = None
    delivery_person: str | None = None
    overtime_cost_request: str | None = None
    base_hours_min: float | None = 140.0
    base_hours_std: float | None = 160.0
    base_hours_max: float | None = 180.0
    members: List[DeliveryMemberSchema]

class DeliverySubmitSchema(BaseModel):
    delivery_month: str  # e.g. 2025-06
    details: List[DeliveryDetailSchema]

class DeliverySummaryCreate(BaseModel):
    delivery_month: str

# ------------------ API ------------------

@router.post("/newsummaries")
async def create_delivery_summary(summary: DeliverySummaryCreate, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Login required")
    title_str = f"{summary.delivery_month} Delivery"
    new_summary = DeliverySummary(
        title=title_str,
        month=summary.delivery_month,
        created_by=current_user.id
    )
    db.add(new_summary)
    await db.commit()
    await db.refresh(new_summary)
    return new_summary

@router.get("/months")
async def get_delivery_months(db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Login required")

    stmt = select(DeliverySummary).order_by(DeliverySummary.month.desc())
    result = await db.execute(stmt)
    summaries = result.scalars().all()

    return [{"id": s.id, "delivery_month": s.month} for s in summaries]

@router.get("/{summary_id}")
async def get_delivery_summary_details(summary_id: int, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Login required")

    stmt = select(DeliveryDetail).where(DeliveryDetail.summary_id == summary_id)
    result = await db.execute(stmt)
    details = result.scalars().all()

    results = []
    for detail in details:
        members_stmt = select(DeliveryMember).where(DeliveryMember.delivery_id == detail.id)
        member_result = await db.execute(members_stmt)
        members = member_result.scalars().all()

        total_people = sum(float(m.work_ratio) for m in members)

        results.append({
            "id": detail.id,
            "project_name": detail.project_name,
            "contract_number": detail.contract_number,
            "delivery_date": str(detail.delivery_date),
            "delivery_status": detail.delivery_status,
            "number_of_people": total_people,
            "contract_start": str(detail.contract_start) if detail.contract_start else None,
            "contract_end": str(detail.contract_end) if detail.contract_end else None,
            "delivery_person": detail.delivery_person_name,
            "overtime_cost_request": detail.overtime_cost_request,
            "base_hours_min": detail.base_hours_min,
            "base_hours_std": detail.base_hours_std,
            "base_hours_max": detail.base_hours_max,
            "created_by": detail.created_by,
            "members": [
                {
                    "member_name": m.member_name,
                    "unit_price": m.unit_price,
                    "total_hours": m.monthly_hours,
                    "work_ratio": float(m.work_ratio)
                } for m in members
            ]
        })

    return results

@router.post("/submit")
async def submit_delivery_data(data: DeliverySubmitSchema, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Login required")

    summary = DeliverySummary(month=data.delivery_month, created_by=current_user.id, title=f"{data.delivery_month} Delivery")
    db.add(summary)
    await db.flush()

    for detail in data.details:
        d = DeliveryDetail(
            summary_id=summary.id,
            project_name=detail.project_name,
            contract_number=detail.contract_number,
            delivery_date=datetime.strptime(detail.delivery_date, "%Y-%m-%d"),
            delivery_status=detail.delivery_status,
            contract_start=datetime.strptime(detail.contract_start, "%Y-%m-%d") if detail.contract_start else None,
            contract_end=datetime.strptime(detail.contract_end, "%Y-%m-%d") if detail.contract_end else None,
            delivery_person_name=detail.delivery_person,
            overtime_cost_request=detail.overtime_cost_request,
            base_hours_min=detail.base_hours_min,
            base_hours_std=detail.base_hours_std,
            base_hours_max=detail.base_hours_max,
            created_by=current_user.id
        )
        db.add(d)
        await db.flush()

        for m in detail.members:
            db.add(DeliveryMember(
                delivery_id=d.id,
                member_name=m.member_name,
                unit_price=m.unit_price,
                monthly_hours=m.total_hours,
                work_ratio=m.work_ratio
            ))

    await db.commit()
    return {"message": "Delivery data has been registered"}

@router.post("/summaries/{summary_id}/details")
async def add_delivery_detail(summary_id: int, detail: DeliveryDetailSchema, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Login required")

    d = DeliveryDetail(
        summary_id=summary_id,
        project_name=detail.project_name,
        contract_number=detail.contract_number,
        delivery_date=datetime.strptime(detail.delivery_date, "%Y-%m-%d"),
        delivery_status=detail.delivery_status,
        contract_start=datetime.strptime(detail.contract_start, "%Y-%m-%d") if detail.contract_start else None,
        contract_end=datetime.strptime(detail.contract_end, "%Y-%m-%d") if detail.contract_end else None,
        delivery_person_name=detail.delivery_person,
        overtime_cost_request=detail.overtime_cost_request,
        base_hours_min=detail.base_hours_min,
        base_hours_std=detail.base_hours_std,
        base_hours_max=detail.base_hours_max,
        created_by=current_user.id
    )
    db.add(d)
    await db.flush()

    for m in detail.members:
        db.add(DeliveryMember(
            delivery_id=d.id,
            member_name=m.member_name,
            unit_price=m.unit_price,
            monthly_hours=m.total_hours,
            work_ratio=m.work_ratio
        ))

    await db.commit()
    return {"message": "Detail has been added"}

@router.put("/details/{detail_id}")
async def update_delivery_detail(detail_id: int, detail: DeliveryDetailSchema, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Login required")

    existing = await db.get(DeliveryDetail, detail_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Data not found")

    if existing.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="No permission to edit")

    existing.project_name = detail.project_name
    existing.contract_number = detail.contract_number
    existing.delivery_date = datetime.strptime(detail.delivery_date.split(" ")[0], "%Y-%m-%d")
    existing.delivery_status = detail.delivery_status
    existing.contract_start = datetime.strptime(detail.contract_start.split(" ")[0], "%Y-%m-%d") if detail.contract_start else None
    existing.contract_end = datetime.strptime(detail.contract_end.split(" ")[0], "%Y-%m-%d") if detail.contract_end else None
    existing.delivery_person_name = detail.delivery_person
    existing.overtime_cost_request = detail.overtime_cost_request
    existing.base_hours_min = detail.base_hours_min
    existing.base_hours_std = detail.base_hours_std
    existing.base_hours_max = detail.base_hours_max

    await db.execute(
        DeliveryMember.__table__.delete().where(DeliveryMember.delivery_id == detail_id)
    )

    for m in detail.members:
        db.add(DeliveryMember(
            delivery_id=detail_id,
            member_name=m.member_name,
            unit_price=m.unit_price,
            monthly_hours=m.total_hours,
            work_ratio=m.work_ratio
        ))

    await db.commit()
    return {"message": "Detail has been updated"}

@router.delete("/details/{detail_id}")
async def delete_delivery_detail(detail_id: int, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Login required")

    existing = await db.get(DeliveryDetail, detail_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Data not found")

    if existing.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="No permission to delete")

    await db.delete(existing)
    await db.commit()
    return {"message": "Detail has been deleted"}
