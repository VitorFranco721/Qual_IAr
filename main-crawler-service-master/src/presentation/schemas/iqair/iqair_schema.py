from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class IQAirDataSchema(BaseModel):
    """Schema para retornar dados coletados do IQAir estruturados"""
    aqi_score: int
    aqi_category: str
    local_time: str
    main_pollutant: str
    pollutant_concentration: str
    temperature: str
    wind_speed: str
    wind_direction: str
    wind_direction_degree: str
    humidity: str
    has_rain: str
    rain_chance: str
    pressure: str
    feels_like: str
    visibility: str
    dew_point: str
    sensor_location: str = ""
    
    class Config:
        from_attributes = True


class IQAirDataResponseSchema(IQAirDataSchema):
    """Schema para resposta com dados completos incluindo ID e timestamps"""
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
