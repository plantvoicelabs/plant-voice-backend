from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime

class PlantMessage(BaseModel):
    id: str
    timestamp: datetime
    message_type: str  # "greeting_morning", "greeting_night", "report"
    text: str
    audio_file: str
    sensor_data: Dict
    analysis: Dict

class DashboardData(BaseModel):
    plant_name: str
    latest_message: Optional[PlantMessage] = None
    current_sensors: Dict
    is_sleeping: bool  # True if between 22:01 - 05:59
    next_update: Optional[str] = None