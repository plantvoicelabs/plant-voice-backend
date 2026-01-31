from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

# Password dari environment variable
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "plantvoice-default-change-me")

class PhaseUpdateRequest(BaseModel):
    phase: str
    password: str

@router.get("/current-phase")
async def get_current_phase():
    """Get current growth phase (public endpoint)"""
    from app.services.growth_phase import get_current_phase, get_all_phases
    
    phase = get_current_phase()
    return {
        "success": True,
        "phase": phase["name"],
        "updated_at": phase["updated_at"],
        "duration_days": phase["duration_days"],
        "optimal_ranges": {
            "temperature": phase["temperature"],
            "humidity": phase["humidity"],
            "light": phase["light"],
            "soil_moisture": phase["soil_moisture"]
        },
        "description": phase["description"],
        "physiological_processes": phase["physiological_processes"],
        "visual_indicators": phase["visual_indicators"],
        "transition_signs": phase["transition_signs"],
        "common_problems": phase["common_problems"],
        "tips": phase["tips"],
        "available_phases": get_all_phases()
    }

@router.post("/update-phase")
async def update_phase(request: PhaseUpdateRequest):
    """Update growth phase (requires password)"""
    
    # Verify password
    if request.password != ADMIN_PASSWORD:
        logger.warning("Invalid password attempt for phase update")
        raise HTTPException(status_code=401, detail="Invalid password")
    
    # Validate and update phase
    from app.services.growth_phase import update_phase as do_update, get_all_phases
    
    valid_phases = get_all_phases()
    if request.phase not in valid_phases:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid phase. Must be one of: {', '.join(valid_phases)}"
        )
    
    try:
        data = do_update(request.phase)
        logger.info(f"Phase updated to: {request.phase}")
        return {
            "success": True,
            "message": f"Phase updated to {request.phase}",
            "data": data
        }
    except Exception as e:
        logger.error(f"Failed to update phase: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class ManualLightRequest(BaseModel):
    light_value: float
    password: str

@router.post("/manual-light")
async def set_manual_light(request: ManualLightRequest):
    """Manually set light value when sensor is broken"""
    
    # Verify password
    if request.password != ADMIN_PASSWORD:
        logger.warning("Invalid password attempt for manual light input")
        raise HTTPException(status_code=401, detail="Invalid password")
    
    try:
        from app.services.influxdb import influxdb_service
        from app.schemas import SensorPayload
        from datetime import datetime
        import pytz
        
        # Create manual sensor data
        manual_data = {
            "device_id": "PVL-001",
            "timestamp": datetime.now(pytz.timezone('Asia/Jakarta')).isoformat(),
            "sensors": {
                "light": {
                    "value": request.light_value,
                    "unit": "lux",
                    "status": "manual_override"
                }
            }
        }
        
        # Write to InfluxDB
        payload = SensorPayload(**manual_data)
        success = influxdb_service.write_sensor_data(payload)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to write to database")
        
        logger.info(f"Manual light value set: {request.light_value} lux")
        return {
            "success": True,
            "message": "Manual light value recorded",
            "light_value": request.light_value,
            "unit": "lux"
        }
    
    except Exception as e:
        logger.error(f"Failed to set manual light: {e}")
        raise HTTPException(status_code=500, detail=str(e))