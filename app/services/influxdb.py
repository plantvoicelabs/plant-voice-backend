from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from app.config import settings
from app.models import SensorPayload
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

class InfluxDBService:
    def __init__(self):
        self.client = InfluxDBClient(
            url=settings.INFLUXDB_URL,
            token=settings.INFLUXDB_TOKEN,
            org=settings.INFLUXDB_ORG
        )
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        self.bucket = settings.INFLUXDB_BUCKET
    
    def write_sensor_data(self, payload: SensorPayload) -> bool:
        try:
            points = []
            
            # Convert timestamp to UTC datetime
            dt = datetime.now(timezone.utc)
            
            # Create point for each sensor
            for sensor_name, sensor_data in payload.sensors.dict().items():
                point = Point("sensor_readings") \
                    .tag("device_id", payload.device_id) \
                    .tag("sensor_type", sensor_name) \
                    .field("value", sensor_data["value"]) \
                    .field("unit", sensor_data["unit"]) \
                    .field("status", sensor_data["status"]) \
                    .time(dt)
                
                points.append(point)
            
            # Write all points
            self.write_api.write(
                bucket=self.bucket,
                org=settings.INFLUXDB_ORG,
                record=points
            )
            
            logger.info(f"Successfully wrote {len(points)} points for device {payload.device_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to write to InfluxDB: {e}")
            return False
    
    def close(self):
        self.client.close()

# Singleton instance
influxdb_service = InfluxDBService()