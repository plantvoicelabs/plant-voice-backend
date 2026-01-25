import httpx
import logging
import os
import uuid
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)

class TTSService:
    def __init__(self):
        self.api_key = settings.ELEVENLABS_API_KEY
        self.base_url = "https://api.elevenlabs.io/v1"
        self.voice_id = "EXAVITQu4vr4xnSDxMaL"  # Bella - soft, gentle voice
        self.model_id = "eleven_multilingual_v2"
        self.audio_dir = os.path.join(os.path.dirname(__file__), "..", "..", "audio_files")
        
        # Create audio directory if not exists
        os.makedirs(self.audio_dir, exist_ok=True)
    
    def generate_speech(self, text: str) -> Optional[str]:
        try:
            url = f"{self.base_url}/text-to-speech/{self.voice_id}"
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }
            
            payload = {
                "text": text,
                "model_id": self.model_id,
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                    "style": 0.5,
                    "use_speaker_boost": True
                }
            }
            
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                
                # Generate unique filename
                filename = f"{uuid.uuid4()}.mp3"
                filepath = os.path.join(self.audio_dir, filename)
                
                # Save audio file
                with open(filepath, "wb") as f:
                    f.write(response.content)
                
                logger.info(f"Audio generated: {filename}")
                return filename
        
        except Exception as e:
            logger.error(f"TTS error: {e}")
            return None
    
    def get_audio_path(self, filename: str) -> Optional[str]:
        filepath = os.path.join(self.audio_dir, filename)
        if os.path.exists(filepath):
            return filepath
        return None
    
    def delete_audio(self, filename: str) -> bool:
        try:
            filepath = os.path.join(self.audio_dir, filename)
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete audio: {e}")
            return False

tts_service = TTSService()