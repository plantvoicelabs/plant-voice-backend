from fastapi import APIRouter, HTTPException, Header, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Optional
from app.services.ai_engine import ai_engine
from app.services.tts import tts_service
from app.config import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/speech", tags=["speech"])

class SpeakRequest(BaseModel):
    plant_name: str
    sensor_data: Dict

class SpeakResponse(BaseModel):
    success: bool
    plant: Optional[str] = None
    text: Optional[str] = None
    audio_file: Optional[str] = None
    analysis: Optional[Dict] = None
    error: Optional[str] = None

@router.post("/speak", response_model=SpeakResponse)
async def generate_plant_speech(
    request: SpeakRequest,
    x_api_key: str = Header(None)
):
    if x_api_key != settings.API_SECRET_KEY:
        logger.warning("Invalid API key attempt for speech endpoint")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    # Get AI response first
    ai_result = ai_engine.generate_plant_response(
        plant_name=request.plant_name,
        sensor_data=request.sensor_data
    )
    
    if not ai_result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ai_result.get("error", "Failed to generate AI response")
        )
    
    text_response = ai_result.get("message")
    
    # Generate speech from text
    audio_filename = tts_service.generate_speech(text_response)
    
    if not audio_filename:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate speech audio"
        )
    
    return SpeakResponse(
        success=True,
        plant=ai_result.get("plant"),
        text=text_response,
        audio_file=audio_filename,
        analysis=ai_result.get("analysis")
    )

@router.get("/audio/{filename}")
async def get_audio_file(filename: str):
    audio_path = tts_service.get_audio_path(filename)
    
    if not audio_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file not found"
        )
    
    return FileResponse(
        path=audio_path,
        media_type="audio/mpeg",
        headers={"Content-Disposition": "inline"}
    )