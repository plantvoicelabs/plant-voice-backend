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
        self.latest_insight = None
        self.latest_comparison = None
        self.messages_file = os.path.join(os.path.dirname(__file__), "..", "..", "messages.json")
        self.insights_file = os.path.join(os.path.dirname(__file__), "..", "..", "insights.json")
        self.comparison_file = os.path.join(os.path.dirname(__file__), "..", "..", "comparison.json")
        self.device_id = "PVL-001"
        self._load_latest_message()
        self._load_latest_insight()
        self._load_latest_comparison()
    
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
    
    def _load_latest_insight(self):
        try:
            if os.path.exists(self.insights_file):
                with open(self.insights_file, "r", encoding="utf-8") as f:
                    self.latest_insight = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load latest insight: {e}")
            self.latest_insight = None
    
    def _save_latest_insight(self):
        try:
            with open(self.insights_file, "w", encoding="utf-8") as f:
                json.dump(self.latest_insight, f, default=str)
        except Exception as e:
            logger.error(f"Failed to save latest insight: {e}")
    
    def _load_latest_comparison(self):
        try:
            if os.path.exists(self.comparison_file):
                with open(self.comparison_file, "r", encoding="utf-8") as f:
                    self.latest_comparison = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load latest comparison: {e}")
            self.latest_comparison = None
    
    def _save_latest_comparison(self):
        try:
            with open(self.comparison_file, "w", encoding="utf-8") as f:
                json.dump(self.latest_comparison, f, default=str)
        except Exception as e:
            logger.error(f"Failed to save latest comparison: {e}")
    
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
    
    def get_latest_insight(self):
        return self.latest_insight
    
    def get_latest_comparison(self):
        return self.latest_comparison
    
    async def generate_growth_comparison(self):
        """Generate daily growth comparison with benchmark"""
        try:
            from app.services.influxdb import influxdb_service
            from app.services.pattern_analyzer import pattern_analyzer
            from app.services.growth_comparator import growth_comparator
            from app.services.growth_phase import get_current_phase
            from app.routes.dashboard import get_experiment_day
            
            logger.info("Generating growth comparison...")
            
            # Get hourly data for last 24 hours (for sensor averages)
            hourly_data = influxdb_service.get_hourly_stats(self.device_id, hours=24)
            
            if not hourly_data:
                logger.warning("No hourly data available for comparison")
                return
            
            # Get daily data for GDD calculation
            daily_data = influxdb_service.get_daily_stats(self.device_id, days=7)
            
            # Analyze patterns to get sensor stats
            pattern_analysis = pattern_analyzer.analyze_daily_patterns(hourly_data)
            sensor_stats = pattern_analysis.get("sensors", {})
            
            # Get current phase
            phase = get_current_phase()
            
            # Get experiment day
            experiment_day = get_experiment_day()
            
            # Calculate accumulated GDD
            daily_temps = []
            for record in daily_data:
                if record.get("sensor_type") == "temperature":
                    daily_temps.append(record.get("value", 0))
            
            accumulated_gdd = growth_comparator.calculate_accumulated_gdd(daily_temps)
            
            # Compare with benchmark
            comparisons = growth_comparator.compare_with_benchmark(
                sensor_stats=sensor_stats,
                phase_data=phase,
                experiment_day=experiment_day,
                accumulated_gdd=accumulated_gdd
            )
            
            # Calculate overall score
            overall = growth_comparator.calculate_overall_score(comparisons)
            
            # Generate recommendation
            recommendation = growth_comparator.generate_recommendation(comparisons, phase)
            
            # Save comparison
            self.latest_comparison = {
                "id": str(uuid.uuid4()),
                "timestamp": datetime.now(pytz.timezone('Asia/Jakarta')).isoformat(),
                "experiment_day": experiment_day,
                "phase": phase["name"],
                "comparisons": comparisons,
                "overall_score": overall["score"],
                "overall_status": overall["status"],
                "recommendation": recommendation,
                "accumulated_gdd": accumulated_gdd
            }
            
            self._save_latest_comparison()
            logger.info(f"Growth comparison generated. Score: {overall['score']}/100")
            
        except Exception as e:
            logger.error(f"Growth comparison generation error: {e}")
    
    async def generate_daily_insight(self):
        """Generate daily AI insight from pattern analysis"""
        try:
            from app.services.influxdb import influxdb_service
            from app.services.pattern_analyzer import pattern_analyzer
            from app.services.ai_engine import ai_engine
            from app.services.growth_phase import get_current_phase
            
            logger.info("Generating daily insight...")
            
            # Get hourly data for last 24 hours
            hourly_data = influxdb_service.get_hourly_stats(self.device_id, hours=24)
            
            if not hourly_data:
                logger.warning("No hourly data available for daily insight")
                return
            
            # Analyze patterns
            pattern_analysis = pattern_analyzer.analyze_daily_patterns(hourly_data)
            
            if not pattern_analysis.get("success"):
                logger.error(f"Pattern analysis failed: {pattern_analysis.get('error')}")
                return
            
            # Get current phase
            phase = get_current_phase()
            
            # Generate AI insight
            insight_result = ai_engine.generate_daily_insight(pattern_analysis, phase)
            
            if not insight_result.get("success"):
                logger.error(f"Insight generation failed: {insight_result.get('error')}")
                return
            
            # Save insight
            self.latest_insight = {
                "id": str(uuid.uuid4()),
                "timestamp": datetime.now(pytz.timezone('Asia/Jakarta')).isoformat(),
                "type": "daily",
                "insight": insight_result.get("insight"),
                "analysis": pattern_analysis,
                "phase": phase["name"]
            }
            
            self._save_latest_insight()
            logger.info("Daily insight generated and saved")
            
        except Exception as e:
            logger.error(f"Daily insight generation error: {e}")
    
    async def generate_weekly_insight(self):
        """Generate weekly AI insight from pattern analysis"""
        try:
            from app.services.influxdb import influxdb_service
            from app.services.pattern_analyzer import pattern_analyzer
            from app.services.ai_engine import ai_engine
            from app.services.growth_phase import get_current_phase
            
            logger.info("Generating weekly insight...")
            
            # Get daily data for last 7 days
            daily_data = influxdb_service.get_daily_stats(self.device_id, days=7)
            
            if not daily_data:
                logger.warning("No daily data available for weekly insight")
                return
            
            # Analyze patterns
            pattern_analysis = pattern_analyzer.analyze_weekly_patterns(daily_data)
            
            if not pattern_analysis.get("success"):
                logger.error(f"Weekly pattern analysis failed: {pattern_analysis.get('error')}")
                return
            
            # Get current phase
            phase = get_current_phase()
            
            # Generate AI insight
            insight_result = ai_engine.generate_weekly_insight(pattern_analysis, phase)
            
            if not insight_result.get("success"):
                logger.error(f"Weekly insight generation failed: {insight_result.get('error')}")
                return
            
            # Save insight
            self.latest_insight = {
                "id": str(uuid.uuid4()),
                "timestamp": datetime.now(pytz.timezone('Asia/Jakarta')).isoformat(),
                "type": "weekly",
                "insight": insight_result.get("insight"),
                "analysis": pattern_analysis,
                "phase": phase["name"]
            }
            
            self._save_latest_insight()
            logger.info("Weekly insight generated and saved")
            
        except Exception as e:
            logger.error(f"Weekly insight generation error: {e}")
    
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
        jakarta_tz = pytz.timezone('Asia/Jakarta')
        
        # Morning greeting - 06:00 WIB
        self.scheduler.add_job(
            self.generate_scheduled_message,
            CronTrigger(hour=6, minute=0, timezone=jakarta_tz),
            args=["greeting_morning"],
            id="greeting_morning"
        )
        
        # Regular reports - 08:00, 10:00, 12:00, 14:00, 16:00, 18:00, 20:00 WIB
        for hour in [8, 10, 12, 14, 16, 18, 20]:
            self.scheduler.add_job(
                self.generate_scheduled_message,
                CronTrigger(hour=hour, minute=0, timezone=jakarta_tz),
                args=["report"],
                id=f"report_{hour}"
            )
        
        # Night greeting - 22:00 WIB
        self.scheduler.add_job(
            self.generate_scheduled_message,
            CronTrigger(hour=22, minute=0, timezone=jakarta_tz),
            args=["greeting_night"],
            id="greeting_night"
        )
        
        # Daily insight - 06:05 WIB (after morning greeting)
        self.scheduler.add_job(
            self.generate_daily_insight,
            CronTrigger(hour=6, minute=5, timezone=jakarta_tz),
            id="daily_insight"
        )
        
        # Weekly insight - Monday 06:10 WIB
        self.scheduler.add_job(
            self.generate_weekly_insight,
            CronTrigger(day_of_week='mon', hour=6, minute=10, timezone=jakarta_tz),
            id="weekly_insight"
        )
        
        # Growth comparison - Daily 06:15 WIB
        self.scheduler.add_job(
            self.generate_growth_comparison,
            CronTrigger(hour=6, minute=15, timezone=jakarta_tz),
            id="growth_comparison"
        )
        
        self.scheduler.start()
        logger.info("Plant scheduler started with 12 jobs (9 messages + 2 insights + 1 comparison)")
    
    def stop(self):
        self.scheduler.shutdown()
        logger.info("Plant scheduler stopped")

plant_scheduler = PlantScheduler()