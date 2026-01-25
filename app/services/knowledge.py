import json
import os
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class KnowledgeService:
    def __init__(self):
        self.knowledge_dir = os.path.join(os.path.dirname(__file__), "..", "knowledge")
        self.plants_dir = os.path.join(self.knowledge_dir, "plants")
        self.general_knowledge = self._load_general_knowledge()
        self.plants_cache = {}
    
    def _load_general_knowledge(self) -> Dict:
        try:
            filepath = os.path.join(self.knowledge_dir, "general.json")
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load general knowledge: {e}")
            return {}
    
    def get_plant_knowledge(self, plant_name: str) -> Optional[Dict]:
        plant_name = plant_name.lower()
        
        if plant_name in self.plants_cache:
            return self.plants_cache[plant_name]
        
        try:
            filepath = os.path.join(self.plants_dir, f"{plant_name}.json")
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.plants_cache[plant_name] = data
                return data
        except FileNotFoundError:
            logger.warning(f"Plant knowledge not found: {plant_name}")
            return None
        except Exception as e:
            logger.error(f"Failed to load plant knowledge for {plant_name}: {e}")
            return None
    
    def get_available_plants(self) -> list:
        try:
            files = os.listdir(self.plants_dir)
            return [f.replace(".json", "") for f in files if f.endswith(".json")]
        except Exception as e:
            logger.error(f"Failed to list available plants: {e}")
            return []
    
    def analyze_sensor_reading(self, plant_name: str, sensor_type: str, value: float) -> Dict:
        plant = self.get_plant_knowledge(plant_name)
        
        if not plant:
            return {
                "status": "error",
                "message": f"Unknown plant: {plant_name}"
            }
        
        conditions = plant.get("optimal_conditions", {})
        sensor_config = conditions.get(sensor_type)
        
        if not sensor_config:
            return {
                "status": "error",
                "message": f"Unknown sensor type: {sensor_type}"
            }
        
        optimal_min = sensor_config.get("min")
        optimal_max = sensor_config.get("max")
        critical_low = sensor_config.get("critical_low")
        critical_high = sensor_config.get("critical_high")
        unit = sensor_config.get("unit", "")
        
        # Handle None values
        if value is None:
            return {
                "sensor_type": sensor_type,
                "value": None,
                "unit": unit,
                "status": "error",
                "severity": "warning",
                "optimal_range": {"min": optimal_min, "max": optimal_max},
                "critical_range": {"low": critical_low, "high": critical_high}
            }
        
        # Determine status with None checks
        if critical_low is not None and value < critical_low:
            status = "critical_low"
            severity = "critical"
        elif optimal_min is not None and value < optimal_min:
            status = "low"
            severity = "warning"
        elif critical_high is not None and value > critical_high:
            status = "critical_high"
            severity = "critical"
        elif optimal_max is not None and value > optimal_max:
            status = "high"
            severity = "warning"
        else:
            status = "normal"
            severity = "normal"
        
        return {
            "sensor_type": sensor_type,
            "value": value,
            "unit": unit,
            "status": status,
            "severity": severity,
            "optimal_range": {
                "min": optimal_min,
                "max": optimal_max
            },
            "critical_range": {
                "low": critical_low,
                "high": critical_high
            }
        }
    
    def analyze_all_sensors(self, plant_name: str, sensor_data: Dict) -> Dict:
        results = {}
        overall_severity = "normal"
        
        for sensor_type, reading in sensor_data.items():
            if isinstance(reading, dict) and "value" in reading:
                value = reading["value"]
            else:
                value = reading
            
            if value is None:
                results[sensor_type] = {
                    "status": "error",
                    "severity": "warning",
                    "message": "Sensor reading unavailable"
                }
                continue
            
            analysis = self.analyze_sensor_reading(plant_name, sensor_type, value)
            results[sensor_type] = analysis
            
            if analysis.get("severity") == "critical":
                overall_severity = "critical"
            elif analysis.get("severity") == "warning" and overall_severity != "critical":
                overall_severity = "warning"
        
        return {
            "plant": plant_name,
            "overall_severity": overall_severity,
            "sensors": results
        }

knowledge_service = KnowledgeService()