from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime

from src.infrastructure.config.database import Base


class IQAirEntity(Base):
    __tablename__ = "iqair_data"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    aqi_score = Column(Integer, nullable=False)
    aqi_category = Column(String, nullable=True)
    local_time = Column(String, nullable=True)
    main_pollutant = Column(String, nullable=True)
    pollutant_concentration = Column(String, nullable=True)
    temperature = Column(String, nullable=True)
    wind_speed = Column(String, nullable=True)
    wind_direction = Column(String, nullable=True)
    wind_direction_degree = Column(String, nullable=True)
    humidity = Column(String, nullable=True)
    has_rain = Column(String, nullable=True)
    rain_chance = Column(String, nullable=True)
    pressure = Column(String, nullable=True)
    feels_like = Column(String, nullable=True)
    visibility = Column(String, nullable=True)
    dew_point = Column(String, nullable=True)
    sensor_location = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

