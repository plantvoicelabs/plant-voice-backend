from fastapi import APIRouter, HTTPException, Header, status
from pydantic import BaseModel
from typing import Dict, Optional
from app.services.ai_engine import ai_engine
from app.services.knowledge import knowledge_service
from app.config import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/ai", tags=["ai"])

class PlantQueryRequest(BaseModel):
    plant_name: str
    sensor_data: Dict

class PlantQueryResponse(BaseModel):
    success: bool
    plant: Optional[str] = None
    message: Optional[str] = None
    analysis: Optional[Dict] = None
    error: Optional[str] = None

@router.post("/talk", response_model=PlantQueryResponse)
async def get_plant_response(
    request: PlantQueryRequest,
    x_api_key: str = Header(None)
):
    if x_api_key != settings.API_SECRET_KEY:
        logger.warning(f"Invalid API key attempt for AI endpoint")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    result = ai_engine.generate_plant_response(
        plant_name=request.plant_name,
        sensor_data=request.sensor_data
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to generate response")
        )
    
    return PlantQueryResponse(
        success=True,
        plant=result.get("plant"),
        message=result.get("message"),
        analysis=result.get("analysis")
    )

@router.get("/plants")
async def get_available_plants():
    plants = knowledge_service.get_available_plants()
    return {
        "plants": plants,
        "count": len(plants)
    }

@router.get("/plants/{plant_name}")
async def get_plant_info(plant_name: str):
    plant = knowledge_service.get_plant_knowledge(plant_name)
    
    if not plant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plant not found: {plant_name}"
        )
    
    return plant