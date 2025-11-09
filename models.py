"""Database models and schemas"""
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from database import Base

class Prescription(Base):
    __tablename__ = "prescriptions"
    
    prescription_id = Column(Integer, primary_key=True, index=True)
    appointment_id = Column(Integer, nullable=False, index=True)
    patient_id = Column(Integer, nullable=False, index=True)
    doctor_id = Column(Integer, nullable=False, index=True)
    medication = Column(String, nullable=False)
    dosage = Column(String, nullable=False)
    days = Column(Integer, nullable=False)
    issued_at = Column(DateTime(timezone=True), server_default=func.now())

class PrescriptionCreate(BaseModel):
    appointment_id: int
    patient_id: int
    doctor_id: int
    medication: str
    dosage: str
    days: int

class PrescriptionResponse(BaseModel):
    prescription_id: int
    appointment_id: int
    patient_id: int
    doctor_id: int
    medication: str
    dosage: str
    days: int
    issued_at: datetime
    
    class Config:
        from_attributes = True

