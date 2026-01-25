import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import pytz
import uuid
import json
import os

logger = logging.getLogger(__name__)

class PlantScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler(timezone=pytz.timezone('Asia/Jakarta'))
        self.latest_message = None
        self.messages_file = os.path.join(os.path.dirname(__file__), "..", "..", "messages.json")
        self.device_id = "PVL-001"
        self._load_latest_message()
    
    def _load_latest_message(self):
        try:
            if os.path.exists(self.messages_file):
                with open(self.messages_file, "r", encoding="utf-8") as f:
                    self.latest_message = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load latest message: {e}")
            self.latest_message = None
    
    def _save_latest_message(self):
        try:
            with open(self.messages_file, "w", encoding="utf-8") as f:
                json.dump(self.latest_message, f, default=str)
        except Exception as e:
            logger.error(f"Failed to save latest message: {e}")
    
    async def generate_scheduled_message(self, message_type: str):
        try:
            from app.services.ai_engine import ai_engine
            from app.services.tts import tts_service
            
            logger.info(f"Generating scheduled message: {message_type}")
            
            # Get latest sensor data from InfluxDB (from ESP32)
            sensor_data = self._get_latest_sensor_data()
            
            if not sensor_data:
                logger.warning("No sensor data available, skipping message generation")
                return
            
            plant_name = "eggplant"
            
            # Generate AI response with context
            ai_result = ai_engine.generate_plant_response_scheduled(
                plant_name=plant_name,
                sensor_data=sensor_data,
                message_type=message_type
            )
            
            if not ai_result.get("success"):
                logger.error(f"AI generation failed: {ai_result.get('error')}")
                return
            
            text_response = ai_result.get("message")
            
            # Generate TTS
            audio_filename = tts_service.generate_speech(text_response)
            
            if not audio_filename:
                logger.error("TTS generation failed")
                return
            
            # Save latest message
            self.latest_message = {
                "id": str(uuid.uuid4()),
                "timestamp": datetime.now(pytz.timezone('Asia/Jakarta')).isoformat(),
                "message_type": message_type,
                "text": text_response,
                "audio_file": audio_filename,
                "sensor_data": sensor_data,
                "analysis": ai_result.get("analysis", {})
            }
            
            self._save_latest_message()
            logger.info(f"Message generated and saved: {message_type}")
            
        except Exception as e:
            logger.error(f"Scheduled message error: {e}")
    
    def _get_latest_sensor_data(self):
        try:
            from app.services.influxdb import influxdb_service
            
            # Query latest data from InfluxDB (sent by ESP32)
            sensor_data = influxdb_service.get_latest_readings(self.device_id)
            
            if sensor_data:
                logger.info(f"Got real sensor data from ESP32: {list(sensor_data.keys())}")
                return sensor_data
            
        except Exception as e:
            logger.error(f"Failed to get sensor data from InfluxDB: {e}")
        
        # Fallback to mock data if ESP32 not connected
        logger.warning("ESP32 not connected, using mock sensor data")
        return {
            "temperature": {"value": 28, "unit": "°C"},
            "humidity": {"value": 65, "unit": "%"},
            "light": {"value": 20000, "unit": "lux"},
            "soil_moisture": {"value": 72, "unit": "%"},
            "ph": {"value": 6.3},
            "tds": {"value": 1100, "unit": "ppm"}
        }
    
    def get_latest_message(self):
        return self.latest_message
    
    def is_sleeping_time(self):
        now = datetime.now(pytz.timezone('Asia/Jakarta'))
        hour = now.hour
        # Sleeping time: 22:01 - 05:59
        return hour >= 22 or hour < 6
    
    def get_next_update_time(self):
        now = datetime.now(pytz.timezone('Asia/Jakarta'))
        hour = now.hour
        
        schedule_hours = [6, 8, 10, 12, 14, 16, 18, 20, 22]
        
        for h in schedule_hours:
            if hour < h:
                return f"{h:02d}:00"
        
        # Next is tomorrow 6:00
        return "06:00"
    
    def start(self):
        # Morning greeting - 06:00
        self.scheduler.add_job(
            self.generate_scheduled_message,
            CronTrigger(hour=6, minute=0),
            args=["greeting_morning"],
            id="greeting_morning"
        )
        
        # Regular reports - 08:00, 10:00, 12:00, 14:00, 16:00, 18:00, 20:00
        for hour in [8, 10, 12, 14, 16, 18, 20]:
            self.scheduler.add_job(
                self.generate_scheduled_message,
                CronTrigger(hour=hour, minute=0),
                args=["report"],
                id=f"report_{hour}"
            )
        
        # Night greeting - 22:00
        self.scheduler.add_job(
            self.generate_scheduled_message,
            CronTrigger(hour=22, minute=0),
            args=["greeting_night"],
            id="greeting_night"
        )
        
        self.scheduler.start()
        logger.info("Plant scheduler started with 9 daily jobs")
    
    def stop(self):
        self.scheduler.shutdown()
        logger.info("Plant scheduler stopped")

plant_scheduler = PlantScheduler()