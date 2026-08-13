from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from datetime import date
import uuid
import json

from app.models.base import User, DailyTransit, GeneratedReport, ReportTypeEnum
from app.api.dependencies import get_current_user
from app.database.session import get_db
from app.schemas.api import HoroscopeResponse, ReportRequest

router = APIRouter()

@router.get("/api/v1/horoscope/daily", response_model=HoroscopeResponse)
def get_daily_horoscope(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    today = date.today()
    transit = db.query(DailyTransit).filter(
        DailyTransit.user_id == current_user.id,
        DailyTransit.date == today
    ).first()

    if not transit:
        raise HTTPException(status_code=404, detail="Horoscope not found for today. It might be generating.")

    return {"date": transit.date, "generated_text": transit.generated_text}

@router.post("/api/v1/bot/chat")
def ask_astro_bot(
    question: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    AI Astro-Bot endpoint.
    """
    if current_user.credits < 1:
        raise HTTPException(status_code=402, detail="Insufficient credits")

    current_user.credits -= 1
    db.commit()

    # In production, pass context + question to OpenAI:
    # response = openai_client.chat.completions.create(...)
    return {"answer": f"Mock answer for: {question} based on chart of {current_user.first_name}"}

@router.post("/api/v1/reports/request")
def request_report(
    request: ReportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cost = 10
    if current_user.credits < cost:
        raise HTTPException(status_code=402, detail="Insufficient credits")

    current_user.credits -= cost

    report_enum = ReportTypeEnum.three_month_transit if request.report_type == '3_month_transit' else ReportTypeEnum.synastry

    new_report = GeneratedReport(
        user_id=current_user.id,
        report_type=report_enum,
        parameters={"requested_date": str(date.today())}
    )
    db.add(new_report)
    db.commit()
    db.refresh(new_report)

    # Trigger PDF generation task via Celery
    from app.tasks.worker import generate_pdf_report_task
    generate_pdf_report_task.delay(str(new_report.id))

    return {"message": "Report generation requested", "report_id": new_report.id}
