import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pytz

logger = logging.getLogger(__name__)

# GDD Base temperature for eggplant
GDD_BASE_TEMP = 10  # °C

# Expected GDD accumulation per phase (based on research)
EXPECTED_GDD = {
    "germination": {"min": 100, "max": 150},
    "seedling": {"min": 250, "max": 400},
    "vegetative": {"min": 600, "max": 900},
    "flowering": {"min": 900, "max": 1200},
    "fruiting": {"min": 1400, "max": 1800}
}

class GrowthComparator:
    def __init__(self):
        self.device_id = "PVL-001"
        self.jakarta_tz = pytz.timezone('Asia/Jakarta')
    
    def calculate_gdd(self, temp_avg: float) -> float:
        """Calculate Growing Degree Days from average temperature"""
        return max(0, temp_avg - GDD_BASE_TEMP)
    
    def calculate_accumulated_gdd(self, daily_temps: List[float]) -> float:
        """Calculate total accumulated GDD from list of daily average temperatures"""
        total_gdd = 0
        for temp in daily_temps:
            total_gdd += self.calculate_gdd(temp)
        return round(total_gdd, 1)
    
    def get_expected_gdd_for_day(self, day: int, phase: str) -> float:
        """Calculate expected GDD for a given experiment day"""
        # Assume average daily GDD of 17 (based on 27°C avg temp)
        avg_daily_gdd = 17
        return day * avg_daily_gdd
    
    def compare_with_benchmark(self, sensor_stats: Dict, phase_data: Dict, experiment_day: int, accumulated_gdd: float) -> Dict:
        """
        Compare current sensor averages with phase benchmarks
        
        Args:
            sensor_stats: Dict with sensor averages from pattern_analyzer
            phase_data: Dict with phase thresholds from growth_phase
            experiment_day: Current day of experiment
            accumulated_gdd: Total GDD accumulated so far
        
        Returns:
            Dict with comparison results
        """
        
        comparisons = {}
        
        # 1. Timeline comparison
        duration = phase_data.get("duration_days", {})
        min_days = duration.get("min", 7)
        max_days = duration.get("max", 14)
        
        if experiment_day <= min_days:
            timeline_status = "on_track"
            timeline_detail = f"Day {experiment_day} of {min_days}-{max_days} expected days"
        elif experiment_day <= max_days:
            timeline_status = "mid_phase"
            timeline_detail = f"Day {experiment_day} of {min_days}-{max_days} expected days"
        else:
            timeline_status = "extended"
            timeline_detail = f"Day {experiment_day} exceeds typical {max_days} days. Consider checking for issues."
        
        comparisons["timeline"] = {
            "current_day": experiment_day,
            "expected_min": min_days,
            "expected_max": max_days,
            "status": timeline_status,
            "detail": timeline_detail
        }
        
        # 2. Temperature comparison
        if "temperature" in sensor_stats:
            temp_avg = sensor_stats["temperature"].get("avg", 0)
            temp_thresholds = phase_data.get("temperature", {})
            optimal_min = temp_thresholds.get("optimal_min", 25)
            optimal_max = temp_thresholds.get("optimal_max", 30)
            optimal_center = (optimal_min + optimal_max) / 2
            
            deviation = self._calculate_deviation(temp_avg, optimal_min, optimal_max, optimal_center)
            status = self._get_status(temp_avg, temp_thresholds, "temperature", phase_data.get("name", ""))
            
            comparisons["temperature"] = {
                "current_avg": round(temp_avg, 1),
                "benchmark_min": optimal_min,
                "benchmark_max": optimal_max,
                "benchmark_optimal": optimal_center,
                "deviation_percent": deviation,
                "status": status,
                "detail": self._get_temp_detail(temp_avg, optimal_min, optimal_max, status)
            }
        
        # 3. Humidity comparison
        if "humidity" in sensor_stats:
            humid_avg = sensor_stats["humidity"].get("avg", 0)
            humid_thresholds = phase_data.get("humidity", {})
            optimal_min = humid_thresholds.get("optimal_min", 70)
            optimal_max = humid_thresholds.get("optimal_max", 90)
            optimal_center = (optimal_min + optimal_max) / 2
            
            deviation = self._calculate_deviation(humid_avg, optimal_min, optimal_max, optimal_center)
            status = self._get_status(humid_avg, humid_thresholds, "humidity", phase_data.get("name", ""))
            
            comparisons["humidity"] = {
                "current_avg": round(humid_avg, 1),
                "benchmark_min": optimal_min,
                "benchmark_max": optimal_max,
                "benchmark_optimal": optimal_center,
                "deviation_percent": deviation,
                "status": status,
                "detail": self._get_humidity_detail(humid_avg, optimal_min, optimal_max, status)
            }
        
        # 4. Soil moisture comparison
        if "soil_moisture" in sensor_stats:
            soil_avg = sensor_stats["soil_moisture"].get("avg", 0)
            soil_thresholds = phase_data.get("soil_moisture", {})
            optimal_min = soil_thresholds.get("optimal_min", 50)
            optimal_max = soil_thresholds.get("optimal_max", 80)
            optimal_center = (optimal_min + optimal_max) / 2
            
            deviation = self._calculate_deviation(soil_avg, optimal_min, optimal_max, optimal_center)
            status = self._get_status(soil_avg, soil_thresholds, "soil_moisture", phase_data.get("name", ""))
            
            comparisons["soil_moisture"] = {
                "current_avg": round(soil_avg, 1),
                "benchmark_min": optimal_min,
                "benchmark_max": optimal_max,
                "benchmark_optimal": optimal_center,
                "deviation_percent": deviation,
                "status": status,
                "detail": self._get_soil_detail(soil_avg, optimal_min, optimal_max, status)
            }
        
        # 5. Light comparison (skip for germination as low light is preferred)
        if "light" in sensor_stats:
            light_avg = sensor_stats["light"].get("avg", 0)
            light_thresholds = phase_data.get("light", {})
            optimal_min = light_thresholds.get("optimal_min", 0)
            optimal_max = light_thresholds.get("optimal_max", 10000)
            optimal_center = (optimal_min + optimal_max) / 2
            
            deviation = self._calculate_deviation(light_avg, optimal_min, optimal_max, optimal_center)
            status = self._get_status(light_avg, light_thresholds, "light", phase_data.get("name", ""))
            
            comparisons["light"] = {
                "current_avg": round(light_avg, 1),
                "benchmark_min": optimal_min,
                "benchmark_max": optimal_max,
                "benchmark_optimal": optimal_center,
                "deviation_percent": deviation,
                "status": status,
                "detail": self._get_light_detail(light_avg, optimal_min, optimal_max, status, phase_data.get("name", ""))
            }
        
        # 6. GDD Progress comparison
        expected_gdd = self.get_expected_gdd_for_day(experiment_day, phase_data.get("name", "germination"))
        gdd_deviation = round(((accumulated_gdd - expected_gdd) / expected_gdd) * 100, 1) if expected_gdd > 0 else 0
        
        if gdd_deviation >= -10:
            gdd_status = "on_track"
        elif gdd_deviation >= -25:
            gdd_status = "slightly_behind"
        else:
            gdd_status = "behind"
        
        comparisons["gdd_progress"] = {
            "accumulated": accumulated_gdd,
            "expected": round(expected_gdd, 1),
            "deviation_percent": gdd_deviation,
            "status": gdd_status,
            "detail": f"GDD: {accumulated_gdd} accumulated vs {round(expected_gdd, 1)} expected ({gdd_deviation:+.1f}%)"
        }
        
        return comparisons
    
    def calculate_overall_score(self, comparisons: Dict) -> Dict:
        """Calculate overall health score from comparisons"""
        
        scores = []
        weights = {
            "temperature": 25,
            "humidity": 20,
            "soil_moisture": 25,
            "light": 15,
            "gdd_progress": 15
        }
        
        status_scores = {
            "optimal": 100,
            "on_track": 100,
            "slightly_low": 75,
            "slightly_high": 75,
            "slightly_behind": 75,
            "mid_phase": 90,
            "low": 50,
            "high": 50,
            "behind": 50,
            "extended": 60,
            "critical_low": 20,
            "critical_high": 20
        }
        
        total_weight = 0
        weighted_score = 0
        
        for key, weight in weights.items():
            if key in comparisons:
                status = comparisons[key].get("status", "optimal")
                score = status_scores.get(status, 70)
                weighted_score += score * weight
                total_weight += weight
        
        overall_score = round(weighted_score / total_weight) if total_weight > 0 else 0
        
        if overall_score >= 85:
            overall_status = "excellent"
        elif overall_score >= 70:
            overall_status = "good"
        elif overall_score >= 50:
            overall_status = "fair"
        else:
            overall_status = "poor"
        
        return {
            "score": overall_score,
            "status": overall_status
        }
    
    def generate_recommendation(self, comparisons: Dict, phase_data: Dict) -> str:
        """Generate actionable recommendation based on comparisons"""
        
        issues = []
        
        # Check each sensor
        if "humidity" in comparisons:
            status = comparisons["humidity"].get("status")
            if status in ["low", "slightly_low", "critical_low"]:
                issues.append("Humidity is below optimal. Consider misting or using a humidity dome.")
            elif status in ["high", "slightly_high", "critical_high"]:
                issues.append("Humidity is too high. Improve air circulation to prevent fungal issues.")
        
        if "temperature" in comparisons:
            status = comparisons["temperature"].get("status")
            if status in ["low", "slightly_low", "critical_low"]:
                issues.append("Temperature is below optimal. Consider moving to a warmer location.")
            elif status in ["high", "slightly_high", "critical_high"]:
                issues.append("Temperature is too high. Provide shade or improve ventilation.")
        
        if "soil_moisture" in comparisons:
            status = comparisons["soil_moisture"].get("status")
            if status in ["low", "slightly_low", "critical_low"]:
                issues.append("Soil moisture is low. Water the plant soon.")
            elif status in ["high", "slightly_high", "critical_high"]:
                issues.append("Soil is too wet. Reduce watering to prevent root rot.")
        
        if "gdd_progress" in comparisons:
            status = comparisons["gdd_progress"].get("status")
            if status == "behind":
                issues.append("Growth is slower than expected. Check temperature and overall conditions.")
        
        if not issues:
            return f"All conditions are within optimal range for {phase_data.get('name', 'current')} phase. Keep up the good work!"
        
        return " ".join(issues)
    
    def _calculate_deviation(self, value: float, optimal_min: float, optimal_max: float, optimal_center: float) -> float:
        """Calculate percentage deviation from optimal center"""
        if optimal_center == 0:
            return 0
        return round(((value - optimal_center) / optimal_center) * 100, 1)
    
    def _get_status(self, value: float, thresholds: Dict, sensor_name: str = "", phase_name: str = "") -> str:
        """Determine status based on thresholds"""
        critical_low = thresholds.get("critical_low", 0)
        low = thresholds.get("low", 0)
        optimal_min = thresholds.get("optimal_min", 0)
        optimal_max = thresholds.get("optimal_max", 100)
        high = thresholds.get("high", 100)
        critical_high = thresholds.get("critical_high", 100)
        
        # Special handling for light during germination
        if sensor_name == "light" and phase_name == "germination":
            if value <= optimal_max:
                return "optimal"
            elif value <= high:
                return "slightly_high"
            else:
                return "high"
        
        if value <= critical_low:
            return "critical_low"
        elif value <= low:
            return "low"
        elif value < optimal_min:
            return "slightly_low"
        elif value <= optimal_max:
            return "optimal"
        elif value < high:
            return "slightly_high"
        elif value < critical_high:
            return "high"
        else:
            return "critical_high"
    
    def _get_temp_detail(self, value: float, optimal_min: float, optimal_max: float, status: str) -> str:
        if status == "optimal":
            return f"Temperature {value}°C is within optimal range ({optimal_min}-{optimal_max}°C)"
        elif status in ["slightly_low", "low", "critical_low"]:
            return f"Temperature {value}°C is below optimal range ({optimal_min}-{optimal_max}°C)"
        else:
            return f"Temperature {value}°C is above optimal range ({optimal_min}-{optimal_max}°C)"
    
    def _get_humidity_detail(self, value: float, optimal_min: float, optimal_max: float, status: str) -> str:
        if status == "optimal":
            return f"Humidity {value}% is within optimal range ({optimal_min}-{optimal_max}%)"
        elif status in ["slightly_low", "low", "critical_low"]:
            return f"Humidity {value}% is below optimal range ({optimal_min}-{optimal_max}%)"
        else:
            return f"Humidity {value}% is above optimal range ({optimal_min}-{optimal_max}%)"
    
    def _get_soil_detail(self, value: float, optimal_min: float, optimal_max: float, status: str) -> str:
        if status == "optimal":
            return f"Soil moisture {value}% is within optimal range ({optimal_min}-{optimal_max}%)"
        elif status in ["slightly_low", "low", "critical_low"]:
            return f"Soil moisture {value}% is below optimal range ({optimal_min}-{optimal_max}%)"
        else:
            return f"Soil moisture {value}% is above optimal range ({optimal_min}-{optimal_max}%)"
    
    def _get_light_detail(self, value: float, optimal_min: float, optimal_max: float, status: str, phase_name: str) -> str:
        if phase_name == "germination":
            return f"Light {value} lux. Low light is normal for germination phase."
        if status == "optimal":
            return f"Light {value} lux is within optimal range ({optimal_min}-{optimal_max} lux)"
        elif status in ["slightly_low", "low", "critical_low"]:
            return f"Light {value} lux is below optimal range ({optimal_min}-{optimal_max} lux)"
        else:
            return f"Light {value} lux is above optimal range ({optimal_min}-{optimal_max} lux)"


# Singleton instance
growth_comparator = GrowthComparator()