import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pytz
from statistics import mean, stdev

logger = logging.getLogger(__name__)

class PatternAnalyzer:
    def __init__(self):
        self.device_id = "PVL-001"
        self.jakarta_tz = pytz.timezone('Asia/Jakarta')
    
    def analyze_daily_patterns(self, hourly_data: List[Dict]) -> Dict:
        """Analyze patterns from last 24 hours of data"""
        
        if not hourly_data:
            return {"success": False, "error": "No data available"}
        
        # Organize data by sensor
        sensors = {}
        for record in hourly_data:
            sensor = record["sensor_type"]
            if sensor not in sensors:
                sensors[sensor] = []
            sensors[sensor].append({
                "hour": record["hour"],
                "value": record["value"],
                "time": record["time"]
            })
        
        analysis = {
            "success": True,
            "period": "24h",
            "sensors": {},
            "patterns": [],
            "anomalies": [],
            "correlations": []
        }
        
        # Analyze each sensor
        for sensor_name, data in sensors.items():
            if len(data) < 2:
                continue
                
            values = [d["value"] for d in data if d["value"] is not None]
            
            if not values:
                continue
            
            sensor_analysis = {
                "min": round(min(values), 2),
                "max": round(max(values), 2),
                "avg": round(mean(values), 2),
                "range": round(max(values) - min(values), 2),
                "trend": self._calculate_trend(values),
                "std_dev": round(stdev(values), 2) if len(values) > 1 else 0
            }
            
            # Find peak and low hours
            peak_hour = max(data, key=lambda x: x["value"] if x["value"] else 0)
            low_hour = min(data, key=lambda x: x["value"] if x["value"] else float('inf'))
            
            sensor_analysis["peak_hour"] = peak_hour["hour"]
            sensor_analysis["low_hour"] = low_hour["hour"]
            
            analysis["sensors"][sensor_name] = sensor_analysis
            
            # Detect patterns
            pattern = self._detect_daily_pattern(sensor_name, data)
            if pattern:
                analysis["patterns"].append(pattern)
            
            # Detect anomalies
            anomaly = self._detect_anomaly(sensor_name, values)
            if anomaly:
                analysis["anomalies"].append(anomaly)
        
        # Detect correlations between sensors
        correlations = self._detect_correlations(sensors)
        analysis["correlations"] = correlations
        
        return analysis
    
    def analyze_weekly_patterns(self, daily_data: List[Dict]) -> Dict:
        """Analyze patterns from last 7 days of data"""
        
        if not daily_data:
            return {"success": False, "error": "No data available"}
        
        # Organize data by sensor and date
        sensors = {}
        for record in daily_data:
            sensor = record["sensor_type"]
            if sensor not in sensors:
                sensors[sensor] = []
            sensors[sensor].append({
                "date": record["date"],
                "value": record["value"]
            })
        
        analysis = {
            "success": True,
            "period": "7d",
            "sensors": {},
            "trends": [],
            "patterns": []
        }
        
        for sensor_name, data in sensors.items():
            if len(data) < 2:
                continue
            
            values = [d["value"] for d in data if d["value"] is not None]
            
            if not values:
                continue
            
            # Calculate weekly stats
            sensor_analysis = {
                "min": round(min(values), 2),
                "max": round(max(values), 2),
                "avg": round(mean(values), 2),
                "trend": self._calculate_trend(values),
                "change_percent": self._calculate_change_percent(values)
            }
            
            analysis["sensors"][sensor_name] = sensor_analysis
            
            # Detect weekly trend
            trend_desc = self._describe_weekly_trend(sensor_name, sensor_analysis)
            if trend_desc:
                analysis["trends"].append(trend_desc)
        
        return analysis
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from values"""
        if len(values) < 2:
            return "stable"
        
        first_half = mean(values[:len(values)//2])
        second_half = mean(values[len(values)//2:])
        
        diff_percent = ((second_half - first_half) / first_half) * 100 if first_half != 0 else 0
        
        if diff_percent > 10:
            return "increasing"
        elif diff_percent < -10:
            return "decreasing"
        else:
            return "stable"
    
    def _calculate_change_percent(self, values: List[float]) -> float:
        """Calculate percentage change from first to last value"""
        if len(values) < 2 or values[0] == 0:
            return 0
        return round(((values[-1] - values[0]) / values[0]) * 100, 2)
    
    def _detect_daily_pattern(self, sensor: str, data: List[Dict]) -> Optional[Dict]:
        """Detect recurring daily patterns"""
        
        # Group by time of day
        morning = [d["value"] for d in data if d["hour"] in range(6, 12) and d["value"]]
        afternoon = [d["value"] for d in data if d["hour"] in range(12, 18) and d["value"]]
        evening = [d["value"] for d in data if d["hour"] in range(18, 22) and d["value"]]
        night = [d["value"] for d in data if (d["hour"] >= 22 or d["hour"] < 6) and d["value"]]
        
        patterns = []
        
        # Check for afternoon patterns
        if morning and afternoon:
            morning_avg = mean(morning)
            afternoon_avg = mean(afternoon)
            diff_percent = ((afternoon_avg - morning_avg) / morning_avg) * 100 if morning_avg != 0 else 0
            
            if sensor == "temperature" and diff_percent > 10:
                patterns.append({
                    "sensor": sensor,
                    "type": "daily_cycle",
                    "description": f"Temperature rises in afternoon (avg +{diff_percent:.1f}% from morning)"
                })
            elif sensor == "humidity" and diff_percent < -10:
                patterns.append({
                    "sensor": sensor,
                    "type": "daily_cycle", 
                    "description": f"Humidity drops in afternoon (avg {diff_percent:.1f}% from morning)"
                })
            elif sensor == "light" and diff_percent > 50:
                patterns.append({
                    "sensor": sensor,
                    "type": "daily_cycle",
                    "description": f"Light peaks in afternoon as expected"
                })
        
        return patterns[0] if patterns else None
    
    def _detect_anomaly(self, sensor: str, values: List[float]) -> Optional[Dict]:
        """Detect anomalies in sensor data"""
        
        if len(values) < 3:
            return None
        
        avg = mean(values)
        std = stdev(values) if len(values) > 1 else 0
        
        # Check for values outside 2 standard deviations
        for val in values:
            if std > 0 and abs(val - avg) > 2 * std:
                return {
                    "sensor": sensor,
                    "type": "outlier",
                    "description": f"Unusual {sensor} reading detected: {val:.1f} (avg: {avg:.1f})"
                }
        
        # Check for sudden drops (potential sensor issues)
        for i in range(1, len(values)):
            if values[i-1] != 0:
                change = ((values[i] - values[i-1]) / values[i-1]) * 100
                if abs(change) > 50:
                    return {
                        "sensor": sensor,
                        "type": "sudden_change",
                        "description": f"Sudden {sensor} change detected: {change:.1f}% in one hour"
                    }
        
        return None
    
    def _detect_correlations(self, sensors: Dict) -> List[Dict]:
        """Detect correlations between different sensors"""
        
        correlations = []
        
        # Check temperature-humidity correlation
        if "temperature" in sensors and "humidity" in sensors:
            temp_data = sensors["temperature"]
            humid_data = sensors["humidity"]
            
            # Match by hour
            temp_by_hour = {d["hour"]: d["value"] for d in temp_data if d["value"]}
            humid_by_hour = {d["hour"]: d["value"] for d in humid_data if d["value"]}
            
            common_hours = set(temp_by_hour.keys()) & set(humid_by_hour.keys())
            
            if len(common_hours) >= 3:
                # Simple correlation check
                temp_increases = 0
                humid_decreases = 0
                
                hours_list = sorted(common_hours)
                for i in range(1, len(hours_list)):
                    prev_h = hours_list[i-1]
                    curr_h = hours_list[i]
                    
                    if temp_by_hour[curr_h] > temp_by_hour[prev_h]:
                        temp_increases += 1
                        if humid_by_hour[curr_h] < humid_by_hour[prev_h]:
                            humid_decreases += 1
                
                if temp_increases > 0 and humid_decreases / temp_increases > 0.6:
                    correlations.append({
                        "sensors": ["temperature", "humidity"],
                        "type": "inverse",
                        "description": "When temperature rises, humidity tends to drop (natural inverse correlation)"
                    })
        
        # Check soil moisture trend
        if "soil_moisture" in sensors:
            soil_data = sensors["soil_moisture"]
            values = [d["value"] for d in soil_data if d["value"]]
            
            if len(values) >= 3:
                trend = self._calculate_trend(values)
                if trend == "decreasing":
                    daily_drop = (values[0] - values[-1]) / len(values) if len(values) > 1 else 0
                    if daily_drop > 1:
                        correlations.append({
                            "sensors": ["soil_moisture"],
                            "type": "trend_warning",
                            "description": f"Soil moisture declining at ~{daily_drop:.1f}% per hour. May need watering soon."
                        })
        
        return correlations
    
    def _describe_weekly_trend(self, sensor: str, analysis: Dict) -> Optional[Dict]:
        """Generate description for weekly trends"""
        
        trend = analysis.get("trend")
        change = analysis.get("change_percent", 0)
        
        if abs(change) < 5:
            return None
        
        direction = "increased" if change > 0 else "decreased"
        
        return {
            "sensor": sensor,
            "trend": trend,
            "description": f"{sensor.replace('_', ' ').title()} has {direction} by {abs(change):.1f}% over the past week"
        }

# Singleton instance
pattern_analyzer = PatternAnalyzer()