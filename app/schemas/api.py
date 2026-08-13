from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime, time
import uuid

class UserCreate(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str
    birth_date: date
    birth_time: time
    birth_city: str
    latitude: float
    longitude: float

class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    first_name: str
    last_name: str
    tier: str

    class Config:
        from_attributes = True

class HoroscopeResponse(BaseModel):
    date: date
    generated_text: str

class ReportRequest(BaseModel):
    report_type: str

class PaymentWebhook(BaseModel):
    transaction_id: str
    status: str
    amount: float
