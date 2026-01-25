import httpx
import logging
from typing import Dict
from app.services.knowledge import knowledge_service
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
            plant_knowledge = knowledge_service.get_plant_knowledge(plant_name)
            
            if not plant_knowledge:
                return {
                    "success": False,
                    "error": f"Unknown plant: {plant_name}"
                }
            
            analysis = knowledge_service.analyze_all_sensors(plant_name, sensor_data)
            
            prompt = self._build_prompt(plant_knowledge, sensor_data, analysis, message_type)
            
            response = self._call_openrouter(prompt)
            
            if response is None:
                return {
                    "success": False,
                    "error": "Failed to get response from AI"
                }
            
            return {
                "success": True,
                "plant": plant_name,
                "analysis": analysis,
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
    
    def _build_prompt(self, plant_knowledge: Dict, sensor_data: Dict, analysis: Dict, message_type: str) -> str:
        plant_name = plant_knowledge.get("name", "Plant")
        scientific_name = plant_knowledge.get("scientific_name", "")
        
        sensor_summary = []
        for sensor_type, data in analysis.get("sensors", {}).items():
            if "value" in data:
                status = data.get("status", "unknown")
                value = data.get("value")
                unit = data.get("unit", "")
                optimal = data.get("optimal_range", {})
                sensor_summary.append(
                    f"- {sensor_type}: {value}{unit} (status: {status}, optimal: {optimal.get('min')}-{optimal.get('max')}{unit})"
                )
        
        sensor_text = "\n".join(sensor_summary)
        overall_severity = analysis.get("overall_severity", "normal")
        
        # Context based on message type
        if message_type == "greeting_morning":
            context = """This is a MORNING GREETING (6:00 AM). 
Start by saying good morning and express how you feel waking up. 
Then briefly mention your current conditions and what you need for the day ahead.
Be cheerful and optimistic about the new day."""
        
        elif message_type == "greeting_night":
            context = """This is a NIGHT GREETING (10:00 PM). 
Say good night and summarize how your day was based on the conditions.
Mention if you had a good day or faced challenges.
End by saying you will rest now and see them tomorrow.
Be calm and peaceful."""
        
        else:  # report
            context = """This is a REGULAR STATUS REPORT. 
Share your current condition based on the sensor readings.
If something is wrong, explain what you need.
If everything is good, express gratitude.
Be conversational and helpful."""
        
        prompt = f"""You are a {plant_name} ({scientific_name}) that can talk. Based on the sensor readings below, express how you feel in first person perspective.

MESSAGE TYPE CONTEXT:
{context}

Current sensor readings:
{sensor_text}

Overall condition: {overall_severity}

Guidelines:
- Speak as if you are the plant talking to your caretaker
- If conditions are critical, express urgency but stay friendly
- If conditions are normal, express happiness and gratitude
- Give specific, actionable advice based on the readings
- Keep response concise (2-4 sentences)
- Do not use emojis
- Match your tone to the message type (morning=cheerful, night=peaceful, report=informative)

Now respond as the plant:"""
        
        return prompt

ai_engine = AIEngine()