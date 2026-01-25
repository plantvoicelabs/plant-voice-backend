from pydantic import BaseModel, Field, validator
from typing import Literal

class SensorReading(BaseModel):
    value: float
    unit: str
    status: Literal["low", "normal", "high", "error"] = "normal"

class SensorData(BaseModel):
    temperature: SensorReading
    humidity: SensorReading
    light: SensorReading
    soil_moisture: SensorReading
    tds: SensorReading
    ph: SensorReading

class SensorPayload(BaseModel):
    device_id: str = Field(..., min_length=3, max_length=50)
    timestamp: int = Field(..., gt=0)
    sensors: SensorData
    
    @validator('device_id')
    def validate_device_id(cls, v):
        if not v.startswith('PVL-'):
            raise ValueError('device_id must start with PVL-')
        return v