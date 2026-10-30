import os
from pydantic_settings import BaseSettings

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")
    
    PROJECT_NAME: str = "5G-EdgeAgri"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api"
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./edgeagri.db"
    SYNC_DATABASE_URL: str = "sqlite:///./edgeagri.db"
    
    # MQTT Configuration
    MQTT_BROKER_HOST: str = os.getenv("MQTT_BROKER_HOST", "localhost")
    MQTT_BROKER_PORT: int = int(os.getenv("MQTT_BROKER_PORT", "1883"))
    MQTT_CLIENT_ID: str = "5g-edgeagri-backend"
    MQTT_TOPIC_TELEMETRY: str = "agri/farm/+/sensors"
    MQTT_TOPIC_ALERTS: str = "agri/alerts/+"
    MQTT_TOPIC_ACTUATION: str = "agri/actuators/+"
    
    # Telemetry Simulation Defaults
    TELEMETRY_INTERVAL_SECONDS: float = 2.0
    SIMULATION_ENABLED: bool = True
    
    # 5G Network Simulation Defaults
    DEFAULT_NETWORK_PROFILE: str = "5g_urllc"  # 5g_urllc, 5g_embb, 4g_lte, remote_cloud

settings = Settings()
