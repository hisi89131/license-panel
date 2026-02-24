from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(String, unique=True)
    username = Column(String)
    role = Column(String)  # main_admin / sub_admin
    balance = Column(Float, default=0)


class License(Base):
    __tablename__ = "licenses"

    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True)
    owner_id = Column(String)
    duration_hours = Column(Integer)
    device_limit = Column(Integer)
    device_used = Column(Integer, default=0)
    price = Column(Float)
    expiry = Column(DateTime)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
