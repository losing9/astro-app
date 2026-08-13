from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.database.session import engine, get_db
from app.models.base import Base, User, DailyTransit, GeneratedReport, ReportTypeEnum, Payment, PaymentProviderEnum
from app.schemas.api import UserCreate, UserResponse, HoroscopeResponse, ReportRequest, PaymentWebhook
from app.tasks.worker import generate_daily_horoscope_task
from app.services.auth import get_password_hash
from app.api.routes import router as api_router

# FastAPI App Initialization
app = FastAPI(title="Astrogunluk.tr API", version="1.0.0")

# Database Setup
Base.metadata.create_all(bind=engine)


app.include_router(api_router)

# Endpoints
@app.get("/")
def read_root():
    return {"message": "Welcome to Astrogunluk.tr API"}

@app.post("/api/v1/auth/register", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = get_password_hash(user.password)

    new_user = User(
        email=user.email,
        password_hash=hashed_password,
        first_name=user.first_name,
        last_name=user.last_name,
        birth_date=user.birth_date,
        birth_time=user.birth_time,
        birth_city=user.birth_city,
        latitude=user.latitude,
        longitude=user.longitude
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@app.post("/api/v1/payments/webhook")
def payment_webhook(webhook_data: PaymentWebhook, db: Session = Depends(get_db)):
    """
    Webhook for payment provider (Iyzico/PayTR) to confirm successful transaction.
    """
    print(f"Received webhook for tx: {webhook_data.transaction_id}, status: {webhook_data.status}")
    return {"status": "received"}
