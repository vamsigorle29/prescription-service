"""
Prescription Service - Create and read prescriptions
"""
from fastapi import FastAPI, HTTPException, Depends, Query, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
import structlog
import httpx
import os
from uuid import uuid4

from database import get_db, init_db
from models import Prescription, PrescriptionCreate, PrescriptionResponse

logger = structlog.get_logger()

app = FastAPI(
    title="Prescription Service",
    version="v1",
    description="Prescription management service with appointment validation",
    openapi_url="/v1/openapi.json",
    docs_url="/v1/docs",
    redoc_url="/v1/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

APPOINTMENT_SERVICE_URL = os.getenv("APPOINTMENT_SERVICE_URL", "http://localhost:8004")
NOTIFICATION_SERVICE_URL = os.getenv("NOTIFICATION_SERVICE_URL", "http://localhost:8007")

@app.on_event("startup")
async def startup():
    init_db()

async def verify_appointment(appointment_id: int, patient_id: int, doctor_id: int) -> dict:
    """Verify appointment exists and is completed"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{APPOINTMENT_SERVICE_URL}/v1/appointments/{appointment_id}")
            if response.status_code == 404:
                raise HTTPException(status_code=404, detail="Appointment not found")
            
            appointment = response.json()
            
            # Verify appointment is completed
            if appointment.get("status") != "COMPLETED":
                raise HTTPException(
                    status_code=400,
                    detail=f"Appointment must be COMPLETED to create prescription. Current status: {appointment.get('status')}"
                )
            
            # Verify patient and doctor match
            if appointment.get("patient_id") != patient_id:
                raise HTTPException(status_code=400, detail="Patient ID does not match appointment")
            
            if appointment.get("doctor_id") != doctor_id:
                raise HTTPException(status_code=400, detail="Doctor ID does not match appointment")
            
            return appointment
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise HTTPException(status_code=404, detail="Appointment not found")
            raise HTTPException(status_code=503, detail="Appointment service unavailable")
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            raise HTTPException(status_code=503, detail="Failed to verify appointment")

async def notify_service(event_type: str, data: dict):
    """Send notification to notification service"""
    async with httpx.AsyncClient() as client:
        try:
            await client.post(
                f"{NOTIFICATION_SERVICE_URL}/v1/notifications",
                json={"event_type": event_type, "data": data},
                timeout=5.0
            )
            logger.info("notification_sent", event_type=event_type)
        except Exception as e:
            logger.warning("notification_service_unavailable", event_type=event_type, error=str(e))

@app.post("/v1/prescriptions", response_model=PrescriptionResponse, status_code=201)
async def create_prescription(
    prescription: PrescriptionCreate,
    correlation_id: Optional[str] = Header(None, alias="X-Correlation-ID"),
    db: Session = Depends(get_db)
):
    """Create a new prescription (requires a completed appointment)"""
    if not correlation_id:
        correlation_id = str(uuid4())
    
    # Verify appointment exists and is completed
    appointment = await verify_appointment(
        prescription.appointment_id,
        prescription.patient_id,
        prescription.doctor_id
    )
    
    db_prescription = Prescription(**prescription.dict())
    db.add(db_prescription)
    db.commit()
    db.refresh(db_prescription)
    
    logger.info(
        "prescription_created",
        prescription_id=db_prescription.prescription_id,
        appointment_id=prescription.appointment_id,
        patient_id=prescription.patient_id,
        doctor_id=prescription.doctor_id,
        correlation_id=correlation_id
    )
    
    # Send notification after prescription creation
    await notify_service("PRESCRIPTION_CREATED", {
        "prescription_id": db_prescription.prescription_id,
        "appointment_id": prescription.appointment_id,
        "patient_id": prescription.patient_id,
        "doctor_id": prescription.doctor_id,
        "medication": prescription.medication
    })
    
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

