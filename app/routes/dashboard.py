from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from typing import Dict, Optional, List
from datetime import datetime
import pytz
import logging

from app.services.influxdb import influxdb_service
from app.services.scheduler import plant_scheduler
from app.services.tts import tts_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])

# Device ID (from ESP32)
DEVICE_ID = "PVL-001"
PLANT_NAME = "eggplant"

# Experiment start date 
EXPERIMENT_START_DATE = datetime(2025, 1, 28, tzinfo=pytz.timezone('Asia/Jakarta'))

def get_experiment_day():
    """Calculate current experiment day"""
    now = datetime.now(pytz.timezone('Asia/Jakarta'))
    delta = now - EXPERIMENT_START_DATE
    return delta.days + 1

@router.get("/sensors")
async def get_current_sensors():
    """Get current sensor readings from ESP32"""
    from app.services.growth_phase import get_current_phase, analyze_sensor_for_phase
    
    sensor_data = influxdb_service.get_latest_readings(DEVICE_ID)
    
    if not sensor_data:
        # Return mock data if ESP32 not connected
        sensor_data = {
            "temperature": {"value": 27.5, "unit": "°C"},
            "humidity": {"value": 68, "unit": "%"},
            "light": {"value": 350, "unit": "lux"},
            "soil_moisture": {"value": 72, "unit": "%"},
            "ph": {"value": 6.5, "unit": ""},
            "tds": {"value": 420, "unit": "ppm"}
        }
        is_live = False
    else:
        is_live = True
    
    # Get current growth phase
    phase = get_current_phase()
    
    # Analyze sensors based on current growth phase
    phase_analysis = {}
    sensor_keys = ["temperature", "humidity", "light", "soil_moisture"]
    
    for key in sensor_keys:
        if key in sensor_data and sensor_data[key].get("value") is not None:
            value = sensor_data[key]["value"]
            phase_analysis[key] = analyze_sensor_for_phase(key, value)
    
    # Calculate overall severity
    severities = [s.get("severity", "normal") for s in phase_analysis.values()]
    if "critical" in severities:
        overall_severity = "critical"
    elif "warning" in severities:
        overall_severity = "warning"
    else:
        overall_severity = "normal"
    
    return {
        "success": True,
        "is_live": is_live,
        "device_id": DEVICE_ID,
        "plant_name": PLANT_NAME,
        "experiment_day": get_experiment_day(),
        "timestamp": datetime.now(pytz.timezone('Asia/Jakarta')).isoformat(),
        "sensors": sensor_data,
        "phase": {
            "name": phase["name"],
            "description": phase["description"],
            "tips": phase["tips"]
        },
        "analysis": {
            "sensors": phase_analysis,
            "overall_severity": overall_severity
        }
    }

@router.get("/latest-message")
async def get_latest_message():
    """Get latest AI message and audio"""
    
    message = plant_scheduler.get_latest_message()
    is_sleeping = plant_scheduler.is_sleeping_time()
    next_update = plant_scheduler.get_next_update_time()
    
    if not message:
        return {
            "success": True,
            "has_message": False,
            "is_sleeping": is_sleeping,
            "next_update": next_update,
            "message": None
        }
    
    # Build audio URL
    audio_url = f"/api/v1/speech/audio/{message.get('audio_file')}" if message.get('audio_file') else None
    
    return {
        "success": True,
        "has_message": True,
        "is_sleeping": is_sleeping,
        "next_update": next_update,
        "message": {
            "id": message.get("id"),
            "timestamp": message.get("timestamp"),
            "type": message.get("message_type"),
            "text": message.get("text"),
            "audio_url": audio_url,
            "sensor_data": message.get("sensor_data"),
            "analysis": message.get("analysis")
        }
    }

@router.get("/history")
async def get_sensor_history(hours: int = 24):
    """Get sensor history for charts"""
    
    # Validate hours parameter (24h, 7d=168h, 30d=720h)
    if hours not in [24, 168, 720]:
        hours = 24
    
    history = influxdb_service.get_readings_history(DEVICE_ID, hours)
    
    if not history:
        # Return mock data for demo
        mock_history = _generate_mock_history(hours)
        return {
            "success": True,
            "is_live": False,
            "hours": hours,
            "data": mock_history
        }
    
    # Organize by sensor type
    organized = _organize_history(history)
    
    return {
        "success": True,
        "is_live": True,
        "hours": hours,
        "data": organized
    }

@router.get("/status")
async def get_dashboard_status():
    """Get overall dashboard status"""
    
    is_sleeping = plant_scheduler.is_sleeping_time()
    next_update = plant_scheduler.get_next_update_time()
    latest_message = plant_scheduler.get_latest_message()
    
    # Check if ESP32 is connected (has recent data)
    sensor_data = influxdb_service.get_latest_readings(DEVICE_ID)
    esp32_connected = sensor_data is not None
    
    return {
        "success": True,
        "plant_name": PLANT_NAME,
        "device_id": DEVICE_ID,
        "esp32_connected": esp32_connected,
        "is_sleeping": is_sleeping,
        "next_update": next_update,
        "has_message": latest_message is not None,
        "last_message_time": latest_message.get("timestamp") if latest_message else None
    }

@router.post("/trigger-message")
async def trigger_message_manually(message_type: str = "report"):
    """Manually trigger AI message generation (for testing)"""
    
    if message_type not in ["greeting_morning", "greeting_night", "report"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid message type. Use: greeting_morning, greeting_night, or report"
        )
    
    # Generate message
    await plant_scheduler.generate_scheduled_message(message_type)
    
    # Get the generated message
    message = plant_scheduler.get_latest_message()
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate message"
        )
    
    audio_url = f"/api/v1/speech/audio/{message.get('audio_file')}" if message.get('audio_file') else None
    
    return {
        "success": True,
        "message": {
            "id": message.get("id"),
            "timestamp": message.get("timestamp"),
            "type": message.get("message_type"),
            "text": message.get("text"),
            "audio_url": audio_url
        }
    }

def _generate_mock_history(hours: int) -> Dict:
    """Generate mock history data for demo"""
    import random
    
    data = {
        "labels": [],
        "temperature": [],
        "humidity": [],
        "soil_moisture": [],
        "light": [],
        "ph": [],
        "tds": []
    }
    
    now = datetime.now(pytz.timezone('Asia/Jakarta'))
    
    for i in range(hours, 0, -1):
        hour = now.hour - i
        if hour < 0:
            hour += 24
        data["labels"].append(f"{hour:02d}:00")
        
        data["temperature"].append(round(25 + random.random() * 5, 1))
        data["humidity"].append(round(60 + random.random() * 15, 1))
        data["soil_moisture"].append(round(65 + random.random() * 15, 1))
        data["light"].append(round(15000 + random.random() * 10000, 0))
        data["ph"].append(round(6.0 + random.random() * 0.8, 1))
        data["tds"].append(round(900 + random.random() * 400, 0))
    
    return data

def _organize_history(history: List[Dict]) -> Dict:
    """Organize raw history data by sensor type"""
    from datetime import datetime
    import pytz
    
    data = {
        "labels": [],
        "temperature": [],
        "humidity": [],
        "soil_moisture": [],
        "light": [],
        "ph": [],
        "tds": []
    }
    
    jakarta_tz = pytz.timezone('Asia/Jakarta')
    utc_tz = pytz.UTC
    
    # Group by time
    time_groups = {}
    for record in history:
        time_str = record.get("time", "")
        sensor = record.get("sensor_type")
        value = record.get("value")
        
        # Convert UTC to Jakarta timezone
        try:
            if time_str:
                # Parse UTC time
                if time_str.endswith('Z'):
                    time_str = time_str[:-1]
                utc_time = datetime.fromisoformat(time_str)
                if utc_time.tzinfo is None:
                    utc_time = utc_tz.localize(utc_time)
                # Convert to Jakarta
                jakarta_time = utc_time.astimezone(jakarta_tz)
                time_key = jakarta_time.strftime("%Y-%m-%dT%H:%M")
            else:
                continue
        except Exception as e:
            logger.error(f"Failed to parse time: {time_str}, error: {e}")
            continue
        
        if time_key not in time_groups:
            time_groups[time_key] = {}
        time_groups[time_key][sensor] = value
    
    # Convert to arrays
    for time_key in sorted(time_groups.keys()):
        # Format label as DD/MM HH:MM for better readability
        try:
            dt = datetime.fromisoformat(time_key)
            label = dt.strftime("%d/%m %H:%M")
        except:
            label = time_key[11:16] if len(time_key) > 11 else time_key
        
        data["labels"].append(label)
        
        sensors = time_groups[time_key]
        data["temperature"].append(sensors.get("temperature", 0))
        data["humidity"].append(sensors.get("humidity", 0))
        data["soil_moisture"].append(sensors.get("soil_moisture", 0))
        data["light"].append(sensors.get("light", 0))
        data["ph"].append(sensors.get("ph", 0))
        data["tds"].append(sensors.get("tds", 0))
    
    return data