import httpx
import logging
from typing import Dict
from app.config import settings

logger = logging.getLogger(__name__)

class AIEngine:
    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "anthropic/claude-sonnet-4"
    
    def generate_plant_response(self, plant_name: str, sensor_data: Dict) -> Dict:
        return self._generate_response(plant_name, sensor_data, message_type="report")
    
    def generate_plant_response_scheduled(self, plant_name: str, sensor_data: Dict, message_type: str) -> Dict:
        return self._generate_response(plant_name, sensor_data, message_type=message_type)
    
    def _generate_response(self, plant_name: str, sensor_data: Dict, message_type: str = "report") -> Dict:
        try:
            # Get current growth phase and analyze sensors
            from app.services.growth_phase import get_current_phase, analyze_sensor_for_phase
            
            phase = get_current_phase()
            
            # Get sensor values
            sensor_values = {
                "temperature": sensor_data.get("temperature", {}).get("value"),
                "humidity": sensor_data.get("humidity", {}).get("value"),
                "light": sensor_data.get("light", {}).get("value"),
                "soil_moisture": sensor_data.get("soil_moisture", {}).get("value")
            }
            
            # Analyze each sensor based on current phase
            phase_analysis = {}
            for sensor_name, value in sensor_values.items():
                if value is not None:
                    phase_analysis[sensor_name] = analyze_sensor_for_phase(sensor_name, value)
            
            # Build prompt with phase context
            prompt = self._build_prompt_with_phase(
                plant_name, 
                sensor_data, 
                phase, 
                phase_analysis, 
                message_type
            )
            
            response = self._call_openrouter(prompt)
            
            if response is None:
                return {
                    "success": False,
                    "error": "Failed to get response from AI"
                }
            
            return {
                "success": True,
                "plant": plant_name,
                "phase": phase["name"],
                "analysis": {
                    "phase": phase["name"],
                    "sensors": phase_analysis,
                    "overall_severity": self._get_overall_severity(phase_analysis)
                },
                "message": response
            }
        
        except Exception as e:
            logger.error(f"AI Engine error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _call_openrouter(self, prompt: str) -> str:
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://plantvoicelabs.com",
                "X-Title": "Plant Voice Labs"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 1024
            }
            
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    self.base_url,
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                
                data = response.json()
                return data["choices"][0]["message"]["content"]
        
        except Exception as e:
            logger.error(f"OpenRouter API error: {e}")
            return None
    
    def _build_prompt_with_phase(self, plant_name: str, sensor_data: Dict, phase: Dict, phase_analysis: Dict, message_type: str) -> str:
        
        # Get sensor values
        temp = sensor_data.get("temperature", {}).get("value", "N/A")
        humidity = sensor_data.get("humidity", {}).get("value", "N/A")
        light = sensor_data.get("light", {}).get("value", "N/A")
        soil = sensor_data.get("soil_moisture", {}).get("value", "N/A")
        
        # Get phase analysis status and messages
        temp_analysis = phase_analysis.get("temperature", {})
        humidity_analysis = phase_analysis.get("humidity", {})
        light_analysis = phase_analysis.get("light", {})
        soil_analysis = phase_analysis.get("soil_moisture", {})
        
        # Get threshold info for context
        temp_thresholds = phase.get("temperature", {})
        humidity_thresholds = phase.get("humidity", {})
        light_thresholds = phase.get("light", {})
        soil_thresholds = phase.get("soil_moisture", {})
        
        # Context based on message type
        if message_type == "greeting_morning":
            context = """This is a MORNING GREETING (6:00 AM). 
Start by saying good morning and express how you feel waking up. 
Mention your current growth phase and how you are developing.
Be cheerful and optimistic about the new day."""
        
        elif message_type == "greeting_night":
            context = """This is a NIGHT GREETING (10:00 PM). 
Say good night and summarize how your day was based on the conditions.
Mention your growth phase and any progress you made today.
Be calm and peaceful, ready to rest."""
        
        else:
            context = """This is a REGULAR STATUS REPORT. 
Share your current condition based on the sensor readings.
Mention what phase you are in and how you are developing.
Be conversational and helpful, like talking to a caring friend."""
        
        prompt = f"""You are an eggplant plant that can speak naturally. Generate a friendly, conversational message about your current condition.

═══════════════════════════════════════════════════════════════
CRITICAL CONTEXT - CURRENT GROWTH PHASE: {phase["name"].upper()}
═══════════════════════════════════════════════════════════════

Phase Description: {phase["description"]}

What is happening in this phase: {phase.get("physiological_processes", "N/A")}

Visual indicators of this phase: {phase.get("visual_indicators", "N/A")}

Signs of transitioning to next phase: {phase.get("transition_signs", "N/A")}

Care tips: {phase.get("tips", "N/A")}

═══════════════════════════════════════════════════════════════
OPTIMAL RANGES FOR {phase["name"].upper()} PHASE (Research-Based)
═══════════════════════════════════════════════════════════════

TEMPERATURE:
  - Critical Low (damage): {temp_thresholds.get("critical_low")}°C
  - Low (suboptimal): {temp_thresholds.get("low")}°C
  - Optimal Range: {temp_thresholds.get("optimal_min")} - {temp_thresholds.get("optimal_max")}°C
  - High (stress): {temp_thresholds.get("high")}°C
  - Critical High (damage): {temp_thresholds.get("critical_high")}°C

HUMIDITY:
  - Critical Low: {humidity_thresholds.get("critical_low")}%
  - Low: {humidity_thresholds.get("low")}%
  - Optimal Range: {humidity_thresholds.get("optimal_min")} - {humidity_thresholds.get("optimal_max")}%
  - High: {humidity_thresholds.get("high")}%
  - Critical High: {humidity_thresholds.get("critical_high")}%

LIGHT:
  - Critical Low: {light_thresholds.get("critical_low")} lux
  - Low: {light_thresholds.get("low")} lux
  - Optimal Range: {light_thresholds.get("optimal_min")} - {light_thresholds.get("optimal_max")} lux
  - High: {light_thresholds.get("high")} lux
  - Critical High: {light_thresholds.get("critical_high")} lux

SOIL MOISTURE:
  - Critical Low (wilting): {soil_thresholds.get("critical_low")}%
  - Low: {soil_thresholds.get("low")}%
  - Optimal Range: {soil_thresholds.get("optimal_min")} - {soil_thresholds.get("optimal_max")}%
  - High: {soil_thresholds.get("high")}%
  - Critical High (waterlogging): {soil_thresholds.get("critical_high")}%

═══════════════════════════════════════════════════════════════
CURRENT SENSOR READINGS AND ANALYSIS
═══════════════════════════════════════════════════════════════

Temperature: {temp}°C
  → Status: {temp_analysis.get("status", "unknown")}
  → Assessment: {temp_analysis.get("message", "N/A")}

Humidity: {humidity}%
  → Status: {humidity_analysis.get("status", "unknown")}
  → Assessment: {humidity_analysis.get("message", "N/A")}

Light: {light} lux
  → Status: {light_analysis.get("status", "unknown")}
  → Assessment: {light_analysis.get("message", "N/A")}

Soil Moisture: {soil}%
  → Status: {soil_analysis.get("status", "unknown")}
  → Assessment: {soil_analysis.get("message", "N/A")}

═══════════════════════════════════════════════════════════════
MESSAGE TYPE
═══════════════════════════════════════════════════════════════
{context}

═══════════════════════════════════════════════════════════════
IMPORTANT RULES FOR GENERATING THE MESSAGE
═══════════════════════════════════════════════════════════════

1. Speak as the plant in FIRST PERSON (I, me, my)
2. Be NATURAL and CONVERSATIONAL - like a friendly chat, not a report
3. JUDGE ALL CONDITIONS BASED ON THE CURRENT PHASE - what is optimal for {phase["name"]} phase
4. For {phase["name"]} phase specifically: {phase["description"]}
5. Status meanings:
   - "optimal" = Condition is perfect, express happiness
   - "slightly_low" or "slightly_high" = Minor concern, mention gently
   - "low" or "high" = Needs attention, give soft suggestion
   - "critical_low" or "critical_high" = Urgent, express discomfort and ask for help
6. Keep the message to 2-4 sentences MAXIMUM
7. Do NOT use emojis
8. Do NOT use technical jargon like "lux", "percentage", or exact numbers unless necessary
9. Speak naturally like "I am feeling warm" instead of "Temperature is 32 degrees"
10. If ALL conditions are optimal, simply express happiness and gratitude

═══════════════════════════════════════════════════════════════

Now generate the plant voice message:"""
        
        return prompt
    
    def _get_overall_severity(self, phase_analysis: dict):
        """Determine overall severity from all sensors"""
        severities = [s.get("severity", "normal") for s in phase_analysis.values()]
        
        if "critical" in severities:
            return "critical"
        elif "warning" in severities:
            return "warning"
        return "normal"

ai_engine = AIEngine()