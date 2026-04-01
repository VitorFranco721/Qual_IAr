from src.persistence.entities.iqair.iqair_entity import IQAirEntity
from src.presentation.schemas.iqair.iqair_schema import IQAirDataSchema, IQAirDataResponseSchema


NOT_FOUND_VALUE = "não encontrado"


def _display_value(value: str) -> str:
    text = str(value or "").strip()
    return text if text else NOT_FOUND_VALUE


def iqair_entity_to_schema(entity: IQAirEntity) -> IQAirDataSchema:
    """Convert IQAirEntity to IQAirDataSchema (without ID and timestamps)"""
    return IQAirDataSchema(
        aqi_score=entity.aqi_score,
        aqi_category=_display_value(entity.aqi_category),
        local_time=_display_value(entity.local_time),
        main_pollutant=_display_value(entity.main_pollutant),
        pollutant_concentration=_display_value(entity.pollutant_concentration),
        temperature=_display_value(entity.temperature),
        wind_speed=_display_value(entity.wind_speed),
        wind_direction=_display_value(entity.wind_direction),
        wind_direction_degree=_display_value(entity.wind_direction_degree),
        humidity=_display_value(entity.humidity),
        has_rain=_display_value(entity.has_rain),
        rain_chance=_display_value(entity.rain_chance),
        pressure=_display_value(entity.pressure),
        feels_like=_display_value(entity.feels_like),
        visibility=_display_value(entity.visibility),
        dew_point=_display_value(entity.dew_point),
        sensor_location=entity.sensor_location or ""
    )


def iqair_entity_to_response_schema(entity: IQAirEntity) -> IQAirDataResponseSchema:
    """Convert IQAirEntity to IQAirDataResponseSchema (with ID and timestamps)"""
    return IQAirDataResponseSchema(
        id=entity.id,
        aqi_score=entity.aqi_score,
        aqi_category=_display_value(entity.aqi_category),
        local_time=_display_value(entity.local_time),
        main_pollutant=_display_value(entity.main_pollutant),
        pollutant_concentration=_display_value(entity.pollutant_concentration),
        temperature=_display_value(entity.temperature),
        wind_speed=_display_value(entity.wind_speed),
        wind_direction=_display_value(entity.wind_direction),
        wind_direction_degree=_display_value(entity.wind_direction_degree),
        humidity=_display_value(entity.humidity),
        has_rain=_display_value(entity.has_rain),
        rain_chance=_display_value(entity.rain_chance),
        pressure=_display_value(entity.pressure),
        feels_like=_display_value(entity.feels_like),
        visibility=_display_value(entity.visibility),
        dew_point=_display_value(entity.dew_point),
        sensor_location=entity.sensor_location or "",
        created_at=entity.created_at,
        updated_at=entity.updated_at
    )


def iqair_schema_to_entity(schema: IQAirDataSchema) -> IQAirEntity:
    """Convert IQAirDataSchema to IQAirEntity"""
    return IQAirEntity(
        aqi_score=schema.aqi_score,
        aqi_category=schema.aqi_category,
        local_time=schema.local_time,
        main_pollutant=schema.main_pollutant,
        pollutant_concentration=schema.pollutant_concentration,
        temperature=schema.temperature,
        wind_speed=schema.wind_speed,
        wind_direction=schema.wind_direction,
        wind_direction_degree=schema.wind_direction_degree,
        humidity=schema.humidity,
        has_rain=schema.has_rain,
        rain_chance=schema.rain_chance,
        pressure=schema.pressure,
        feels_like=schema.feels_like,
        visibility=schema.visibility,
        dew_point=schema.dew_point,
        sensor_location=schema.sensor_location
    )

