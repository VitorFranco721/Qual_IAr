import pandas as pd

from br.aqi.normalize import normalize_dataframe


def test_normalize_dataframe_converts_units_and_columns() -> None:
    """Garante conversão de unidade e colunas esperadas na normalização."""
    raw = pd.DataFrame(
        [
            {
                "datetime_utc": "2025-01-01T00:00:00",
                "station_id": "test",
                "station_name": "Test Station",
                "latitude": -15.8,
                "longitude": -47.9,
                "pollutant": "PM2.5",
                "value": 1.5,
                "unit": "mg/m³",
                "avg_period_minutes": 60,
                "source_url": "http://example.com",
                "source_agency": "Test",
                "ingested_at_utc": "2025-01-02T00:00:00",
                "license": None,
                "quality_flag": "ok",
            }
        ]
    )
    norm = normalize_dataframe(raw)
    assert norm.loc[0, "pollutant"] == "pm25"
    # 1.5 mg/m³ * 1000 = 1500 µg/m³
    assert norm.loc[0, "value"] == 1500.0
    assert norm.loc[0, "unit"] == "µg/m³"
    assert "datetime_utc" in norm.columns
    assert "datetime_local" in norm.columns