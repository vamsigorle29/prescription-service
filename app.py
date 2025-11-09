"""
Prescription Service - Create and read prescriptions
"""
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
import structlog

from database import get_db, init_db
from models import Prescription, PrescriptionCreate, PrescriptionResponse

logger = structlog.get_logger()

app = FastAPI(title="Prescription Service", version="v1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    init_db()

@app.post("/v1/prescriptions", response_model=PrescriptionResponse, status_code=201)
def create_prescription(
    prescription: PrescriptionCreate,
    db: Session = Depends(get_db)
):
    """Create a new prescription (requires an appointment)"""
    # Note: In a real system, we'd verify the appointment exists
    # and is COMPLETED
    
    db_prescription = Prescription(**prescription.dict())
    db.add(db_prescription)
    db.commit()
    db.refresh(db_prescription)
    
    logger.info(
        "prescription_created",
        prescription_id=db_prescription.prescription_id,
        appointment_id=prescription.appointment_id
    )
    
    return db_prescription

@app.get("/v1/prescriptions", response_model=List[PrescriptionResponse])
def get_prescriptions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    patient_id: Optional[int] = None,
    appointment_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get prescriptions with filters"""
    query = db.query(Prescription)
    
    if patient_id:
        query = query.filter(Prescription.patient_id == patient_id)
    
    if appointment_id:
        query = query.filter(Prescription.appointment_id == appointment_id)
    
    total = query.count()
    prescriptions = query.order_by(Prescription.issued_at.desc()).offset(skip).limit(limit).all()
    
    logger.info("prescriptions_retrieved", total=total, returned=len(prescriptions))
    return prescriptions

@app.get("/v1/prescriptions/{prescription_id}", response_model=PrescriptionResponse)
def get_prescription(prescription_id: int, db: Session = Depends(get_db)):
    """Get prescription by ID"""
    prescription = db.query(Prescription).filter(Prescription.prescription_id == prescription_id).first()
    
    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")
    
    return prescription

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "prescription-service"}

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("PORT", 8005))
    uvicorn.run(app, host="0.0.0.0", port=port)

