from unittest.mock import MagicMock

from src.business.services.iqair.iqair_controller import IQAirController


def _controller() -> IQAirController:
    return IQAirController(iqair_repository=MagicMock())


def test_wind_degree_is_not_imputed_from_cardinal() -> None:
    controller = _controller()

    data = controller._process_aqi_data(
        text="AQI\n\n17\n\ngood\n\nMain pollutant\n\nPM2.5\n\n3.0 µg/m³\n\n24°\n\n7 km/h\n\n69%",
        wind_direction_override="NNE",
        wind_direction_degree_override="",
    )

    assert data["wind_direction"] == "NNE"
    assert data["wind_direction_degree"] == "não encontrado"


def test_wind_direction_is_not_imputed_from_degree() -> None:
    controller = _controller()

    data = controller._process_aqi_data(
        text="AQI\n\n17\n\ngood\n\nMain pollutant\n\nPM2.5\n\n3.0 µg/m³\n\n24°\n\n7 km/h\n\n69%",
        wind_direction_override="",
        wind_direction_degree_override="24°",
    )

    assert data["wind_direction"] == "não encontrado"
    assert data["wind_direction_degree"] == "não encontrado"


def test_empty_payload_uses_explicit_not_found() -> None:
    controller = _controller()

    data = controller._process_aqi_data(text="")

    assert data["temperature"] == "não encontrado"
    assert data["wind_speed"] == "não encontrado"
    assert data["wind_direction"] == "não encontrado"
    assert data["wind_direction_degree"] == "não encontrado"


def test_wind_degree_equal_to_temperature_is_discarded_without_direction() -> None:
    controller = _controller()

    data = controller._process_aqi_data(
        text="AQI\n\n17\n\ngood\n\nMain pollutant\n\nPM2.5\n\n3.0 µg/m³\n\n24°\n\n7 km/h\n\n69%",
        wind_direction_override="",
        wind_direction_degree_override="24°",
    )

    assert data["temperature"].startswith("24")
    assert data["wind_direction"] == "não encontrado"
    assert data["wind_direction_degree"] == "não encontrado"
