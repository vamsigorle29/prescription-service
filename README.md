# Prescription Service

Microservice for managing prescriptions in the Hospital Management System.

## Overview

The Prescription Service handles creation and retrieval of prescriptions linked to appointments.

## Features

- ✅ Create prescriptions
- ✅ Read prescriptions
- ✅ Filter by patient/appointment
- ✅ API version `/v1`
- ✅ OpenAPI 3.0 documentation

## Quick Start

### Prerequisites

- Python 3.8+
- pip

### Installation

```bash
pip install -r requirements.txt
```

### Running Locally

```bash
python app.py
```

The service will start on `http://localhost:8005`

### Using Docker

```bash
docker build -t prescription-service:latest .
docker run -p 8005:8005 prescription-service:latest
```

### Using Docker Compose

```bash
docker-compose up
```

## API Documentation

Once the service is running, visit:
- Swagger UI: http://localhost:8005/docs
- ReDoc: http://localhost:8005/redoc

## Endpoints

- `POST /v1/prescriptions` - Create a new prescription
- `GET /v1/prescriptions` - List prescriptions (with filters)
- `GET /v1/prescriptions/{prescription_id}` - Get prescription by ID
- `GET /health` - Health check endpoint

## Environment Variables

- `PORT` - Service port (default: 8005)
- `DATABASE_URL` - Database connection string (default: sqlite:///./prescription.db)

## Kubernetes Deployment

```bash
kubectl apply -f k8s/deployment.yaml
```

## Database Schema

**Prescriptions Table:**
- `prescription_id` (Integer, Primary Key)
- `appointment_id` (Integer, Foreign Key)
- `patient_id` (Integer, Foreign Key)
- `doctor_id` (Integer, Foreign Key)
- `medication` (String)
- `dosage` (String)
- `days` (Integer)
- `issued_at` (DateTime)

## Contributing

This is part of a microservices architecture. For integration with other services, see the main Hospital Management System documentation.

## License

Academic use only.

