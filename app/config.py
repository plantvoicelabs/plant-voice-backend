from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # InfluxDB
    INFLUXDB_URL: str
    INFLUXDB_TOKEN: str
    INFLUXDB_ORG: str
    INFLUXDB_BUCKET: str
    
    # API
    API_SECRET_KEY: str
    ALLOWED_DEVICE_IDS: str
    
    # OpenRouter
    OPENROUTER_API_KEY: str
    
    # ElevenLabs
    ELEVENLABS_API_KEY: str
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    @property
    def device_whitelist(self) -> List[str]:
        return [d.strip() for d in self.ALLOWED_DEVICE_IDS.split(",")]
    
    class Config:
        env_file = ".env"

settings = Settings()