from fastapi import APIRouter, HTTPException, Header, status
from app.schemas import SensorPayload
from app.services.influxdb import influxdb_service
from app.config import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/sensors", tags=["sensors"])

@router.post("/data", status_code=status.HTTP_201_CREATED)
async def receive_sensor_data(
    payload: SensorPayload,
    x_api_key: str = Header(None)
):
    # Authentication: Check API Key
    if x_api_key != settings.API_SECRET_KEY:
        logger.warning(f"Invalid API key attempt from device {payload.device_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    # Authorization: Check device whitelist
    if payload.device_id not in settings.device_whitelist:
        logger.warning(f"Unauthorized device attempt: {payload.device_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Device {payload.device_id} not authorized"
        )
    
    # Write to InfluxDB
    success = influxdb_service.write_sensor_data(payload)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to write to database"
        )
    
    return {
        "status": "success",
        "message": f"Data received from {payload.device_id}",
        "timestamp": payload.timestamp
    }

@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Plant Voice Labs IoT Gateway"}