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