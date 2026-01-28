from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.routes import sensors
from app.routes import ai
from app.routes import speech
from app.routes import dashboard
from app.routes import admin
from app.services.scheduler import plant_scheduler
from app.config import settings
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Plant Voice Labs Backend...")
    plant_scheduler.start()
    logger.info("Scheduler started with 9 daily jobs")
    yield
    # Shutdown
    logger.info("Shutting down Plant Voice Labs Backend...")
    plant_scheduler.stop()
    from app.services.influxdb import influxdb_service
    influxdb_service.close()
    logger.info("Shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="Plant Voice Labs IoT Gateway",
    description="Backend API for Plant Voice Labs sensor data ingestion, AI interpretation, and text-to-speech",
    version="3.1.0",
    lifespan=lifespan
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
app.include_router(dashboard.router)
app.include_router(admin.router)

@app.get("/")
async def root():
    return {
        "message": "Plant Voice Labs IoT Gateway",
        "version": "3.1.0",
        "status": "operational",
        "features": [
            "IoT Sensor Data Ingestion",
            "AI Plant Interpretation",
            "Text-to-Speech",
            "Scheduled Messages",
            "Live Dashboard API",
            "Growth Phase Management"
        ]
    }