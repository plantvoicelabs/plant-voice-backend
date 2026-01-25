from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import sensors
from app.routes import ai
from app.routes import speech
from app.config import settings
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Create FastAPI app
app = FastAPI(
    title="Plant Voice Labs IoT Gateway",
    description="Backend API for Plant Voice Labs sensor data ingestion, AI interpretation, and text-to-speech",
    version="3.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(sensors.router)
app.include_router(ai.router)
app.include_router(speech.router)

@app.get("/")
async def root():
    return {
        "message": "Plant Voice Labs IoT Gateway",
        "version": "3.0.0",
        "status": "operational"
    }

@app.on_event("shutdown")
async def shutdown_event():
    from app.services.influxdb import influxdb_service
    influxdb_service.close()