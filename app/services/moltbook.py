import httpx
import logging
from datetime import datetime
import pytz
from app.config import settings

logger = logging.getLogger(__name__)

class MoltbookService:
    def __init__(self):
        self.api_key = settings.MOLTBOOK_API_KEY
        self.base_url = "https://www.moltbook.com/api/v1"
    
    def post_daily_update(self, experiment_day: int, phase_name: str, sensor_data: dict, gdd: float, health_score: int, notable: str = "All stable"):
        """Post daily update to Moltbook"""
        
        try:
            title = f"Day {experiment_day} Update - {phase_name.title()}"
            
            # Get sensor values
            temp = sensor_data.get("temperature", {}).get("avg", 0)
            humid = sensor_data.get("humidity", {}).get("avg", 0)
            soil = sensor_data.get("soil_moisture", {}).get("avg", 0)
            light = sensor_data.get("light", {}).get("avg", 0)
            
            content = f"""📊 Day {experiment_day} Status:
Temp: {temp:.1f}°C | Humidity: {humid:.1f}% | Soil: {soil:.1f}% | Light: {light:.0f} lux
GDD: {gdd:.1f} accumulated
Health Score: {health_score}/100

Notable: {notable}

Dashboard: https://dashboard.plantvoicelabs.com"""
            
            return self._post_to_moltbook(title, content, "general")
        
        except Exception as e:
            logger.error(f"Failed to post daily update to Moltbook: {e}")
            return {"success": False, "error": str(e)}
    
    def post_weekly_summary(self, week_num: int, phase_name: str, weekly_stats: dict, findings: list, anomalies: list, next_expectations: str):
        """Post weekly comprehensive summary to Moltbook"""
        
        try:
            title = f"Week {week_num} Complete: {phase_name.title()} Phase Analysis"
            
            # Format environmental stats
            temp_stats = weekly_stats.get("temperature", {})
            humid_stats = weekly_stats.get("humidity", {})
            soil_stats = weekly_stats.get("soil_moisture", {})
            light_stats = weekly_stats.get("light", {})
            gdd_total = weekly_stats.get("gdd_accumulated", 0)
            health_score = weekly_stats.get("health_score", 0)
            
            # Format findings
            findings_text = "\n".join([f"• {f}" for f in findings])
            
            # Format anomalies
            anomalies_text = "\n".join([f"• {a}" for a in anomalies]) if anomalies else "• None detected"
            
            content = f"""🌱 WEEK {week_num} SUMMARY

Phase: {phase_name.title()} (Day {(week_num-1)*7+1}-{week_num*7})

ENVIRONMENTAL STATS:
- Temperature: {temp_stats.get('min', 0):.1f}-{temp_stats.get('max', 0):.1f}°C (avg: {temp_stats.get('avg', 0):.1f}°C)
- Humidity: {humid_stats.get('min', 0):.1f}-{humid_stats.get('max', 0):.1f}% (avg: {humid_stats.get('avg', 0):.1f}%)
- Soil Moisture: {soil_stats.get('min', 0):.1f}-{soil_stats.get('max', 0):.1f}% (avg: {soil_stats.get('avg', 0):.1f}%)
- Light: {light_stats.get('min', 0):.0f}-{light_stats.get('max', 0):.0f} lux (avg: {light_stats.get('avg', 0):.0f} lux)
- GDD Progress: {gdd_total:.1f} accumulated

HEALTH SCORE: {health_score}/100

KEY FINDINGS:
{findings_text}

ANOMALIES:
{anomalies_text}

NEXT WEEK EXPECTATIONS:
{next_expectations}

Full analysis: https://dashboard.plantvoicelabs.com"""
            
            return self._post_to_moltbook(title, content, "general")
        
        except Exception as e:
            logger.error(f"Failed to post weekly summary to Moltbook: {e}")
            return {"success": False, "error": str(e)}
    
    def _post_to_moltbook(self, title: str, content: str, submolt: str = "general"):
        """Internal method to post to Moltbook API"""
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "submolt": submolt,
                "title": title,
                "content": content
            }
            
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{self.base_url}/posts",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                
                data = response.json()
                logger.info(f"Posted to Moltbook: {title}")
                return data
        
        except Exception as e:
            logger.error(f"Moltbook API error: {e}")
            return None

# Singleton instance
moltbook_service = MoltbookService()