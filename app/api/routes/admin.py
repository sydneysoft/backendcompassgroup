from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.db import get_db
from app.models import Booking, Payment

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/summary")
def summary(db: Session = Depends(get_db)) -> dict:
    bookings = db.scalar(select(func.count()).select_from(Booking)) or 0
    ticketed = db.scalar(select(func.count()).select_from(Booking).where(Booking.status == "ticketed")) or 0
    paid_volume = db.scalar(select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.status == "paid")) or 0
    return {"bookings": bookings, "ticketed": ticketed, "paid_volume": str(paid_volume)}
