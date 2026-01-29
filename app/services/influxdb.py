from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from app.config import settings
from app.schemas import SensorPayload
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
        self.query_api = self.client.query_api()
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
    
    def get_latest_readings(self, device_id: str) -> dict:
        try:
            query = f'''
                from(bucket: "{self.bucket}")
                |> range(start: -1h)
                |> filter(fn: (r) => r["device_id"] == "{device_id}")
                |> filter(fn: (r) => r["_field"] == "value")
                |> last()
            '''
            
            tables = self.query_api.query(query, org=settings.INFLUXDB_ORG)
            
            sensor_data = {}
            
            for table in tables:
                for record in table.records:
                    sensor_type = record.values.get("sensor_type")
                    value = record.get_value()
                    
                    if sensor_type and value is not None:
                        unit = self._get_unit_for_sensor(sensor_type)
                        sensor_data[sensor_type] = {
                            "value": value,
                            "unit": unit
                        }
            
            if sensor_data:
                logger.info(f"Retrieved latest readings for {device_id}: {len(sensor_data)} sensors")
                return sensor_data
            else:
                logger.warning(f"No recent data found for {device_id}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to query InfluxDB: {e}")
            return None
    
    def _get_unit_for_sensor(self, sensor_type: str) -> str:
        units = {
            "temperature": "°C",
            "humidity": "%",
            "light": "lux",
            "soil_moisture": "%",
            "ph": "",
            "tds": "ppm"
        }
        return units.get(sensor_type, "")
    
    def get_readings_history(self, device_id: str, hours: int = 24) -> list:
        try:
            query = f'''
                from(bucket: "{self.bucket}")
                |> range(start: -{hours}h)
                |> filter(fn: (r) => r["device_id"] == "{device_id}")
                |> filter(fn: (r) => r["_field"] == "value")
                |> aggregateWindow(every: 30m, fn: mean, createEmpty: false)
            '''
            
            tables = self.query_api.query(query, org=settings.INFLUXDB_ORG)
            
            history = []
            
            for table in tables:
                for record in table.records:
                    history.append({
                        "time": record.get_time().isoformat(),
                        "sensor_type": record.values.get("sensor_type"),
                        "value": record.get_value()
                    })
            
            logger.info(f"Retrieved {len(history)} historical records for {device_id}")
            return history
            
        except Exception as e:
            logger.error(f"Failed to query history from InfluxDB: {e}")
            return []
    
    def get_hourly_stats(self, device_id: str, hours: int = 24) -> list:
        """Get hourly statistics (min, max, mean) for pattern analysis"""
        try:
            query = f'''
                from(bucket: "{self.bucket}")
                |> range(start: -{hours}h)
                |> filter(fn: (r) => r["device_id"] == "{device_id}")
                |> filter(fn: (r) => r["_field"] == "value")
                |> aggregateWindow(every: 1h, fn: mean, createEmpty: false)
            '''
            
            tables = self.query_api.query(query, org=settings.INFLUXDB_ORG)
            
            hourly_data = []
            
            for table in tables:
                for record in table.records:
                    hourly_data.append({
                        "time": record.get_time().isoformat(),
                        "hour": record.get_time().hour,
                        "sensor_type": record.values.get("sensor_type"),
                        "value": record.get_value()
                    })
            
            logger.info(f"Retrieved {len(hourly_data)} hourly stats for {device_id}")
            return hourly_data
            
        except Exception as e:
            logger.error(f"Failed to get hourly stats: {e}")
            return []
    
    def get_daily_stats(self, device_id: str, days: int = 7) -> list:
        """Get daily statistics for weekly pattern analysis"""
        try:
            query = f'''
                from(bucket: "{self.bucket}")
                |> range(start: -{days}d)
                |> filter(fn: (r) => r["device_id"] == "{device_id}")
                |> filter(fn: (r) => r["_field"] == "value")
                |> aggregateWindow(every: 1d, fn: mean, createEmpty: false)
            '''
            
            tables = self.query_api.query(query, org=settings.INFLUXDB_ORG)
            
            daily_data = []
            
            for table in tables:
                for record in table.records:
                    daily_data.append({
                        "time": record.get_time().isoformat(),
                        "date": record.get_time().strftime("%Y-%m-%d"),
                        "sensor_type": record.values.get("sensor_type"),
                        "value": record.get_value()
                    })
            
            logger.info(f"Retrieved {len(daily_data)} daily stats for {device_id}")
            return daily_data
            
        except Exception as e:
            logger.error(f"Failed to get daily stats: {e}")
            return []
    
    def close(self):
        self.client.close()

# Singleton instance
influxdb_service = InfluxDBService()