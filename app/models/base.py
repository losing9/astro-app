from sqlalchemy import Column, String, Integer, Float, Date, Time, Boolean, ForeignKey, Text, Enum, DateTime
from sqlalchemy import UUID
from sqlalchemy.types import JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid
import datetime
import enum

Base = declarative_base()

class TierEnum(enum.Enum):
    free = 'free'
    premium = 'premium'

class ReportTypeEnum(enum.Enum):
    three_month_transit = '3_month_transit'
    synastry = 'synastry'

class ReportStatusEnum(enum.Enum):
    pending = 'pending'
    processing = 'processing'
    completed = 'completed'
    failed = 'failed'

class PaymentProviderEnum(enum.Enum):
    iyzico = 'iyzico'
    paytr = 'paytr'

class PaymentStatusEnum(enum.Enum):
    success = 'success'
    failed = 'failed'
    pending = 'pending'

class SubscriptionStatusEnum(enum.Enum):
    active = 'active'
    canceled = 'canceled'
    expired = 'expired'


class User(Base):
    __tablename__ = 'users'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    birth_date = Column(Date, nullable=False)
    birth_time = Column(Time, nullable=False)
    birth_city = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    credits = Column(Integer, default=0)
    tier = Column(Enum(TierEnum), default=TierEnum.free)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    natal_charts = relationship("NatalChart", back_populates="user", uselist=False)
    daily_transits = relationship("DailyTransit", back_populates="user")
    reports = relationship("GeneratedReport", back_populates="user")
    payments = relationship("Payment", back_populates="user")
    subscriptions = relationship("Subscription", back_populates="user")


class NatalChart(Base):
    __tablename__ = 'natal_charts'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), unique=True, nullable=False)
    chart_data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User", back_populates="natal_charts")


class DailyTransit(Base):
    __tablename__ = 'daily_transits'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    date = Column(Date, nullable=False)
    transit_data = Column(JSON, nullable=False)
    generated_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User", back_populates="daily_transits")


class GeneratedReport(Base):
    __tablename__ = 'generated_reports'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    report_type = Column(Enum(ReportTypeEnum), nullable=False)
    parameters = Column(JSON, nullable=False)
    pdf_url = Column(String, nullable=True)
    status = Column(Enum(ReportStatusEnum), default=ReportStatusEnum.pending)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User", back_populates="reports")


class Payment(Base):
    __tablename__ = 'payments'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, nullable=False, default="TRY")
    provider = Column(Enum(PaymentProviderEnum), nullable=False)
    transaction_id = Column(String, nullable=False)
    status = Column(Enum(PaymentStatusEnum), default=PaymentStatusEnum.pending)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="payments")


class Subscription(Base):
    __tablename__ = 'subscriptions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    plan_name = Column(String, nullable=False)
    status = Column(Enum(SubscriptionStatusEnum), default=SubscriptionStatusEnum.active)
    start_date = Column(DateTime, default=datetime.datetime.utcnow)
    end_date = Column(DateTime, nullable=False)

    user = relationship("User", back_populates="subscriptions")
