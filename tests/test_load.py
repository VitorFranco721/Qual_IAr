from pathlib import Path

import pandas as pd

from br.aqi.load import load_to_sqlite, read_silver_dataset


def test_read_silver_dataset_and_load_to_sqlite(tmp_path: Path) -> None:
    silver_dir = tmp_path / "silver"
    silver_dir.mkdir()

    df = pd.DataFrame(
        [
            {
                "datetime_utc": "2026-03-01T00:00:00+00:00",
                "datetime_local": "2026-02-29T21:00:00-03:00",
                "station_id": "brasilia",
                "station_name": "Brasília",
                "latitude": -15.7939,
                "longitude": -47.8828,
                "pollutant": "pm25",
                "value": 12.5,
                "unit": "µg/m³",
                "avg_period_minutes": 60,
                "source_url": "crawler.csv",
                "source_agency": "IQAir",
                "ingested_at_utc": "2026-03-01T00:01:00+00:00",
                "license": None,
                "quality_flag": "ok",
            }
        ]
    )
    (silver_dir / "iqair_crawler.csv").write_text(df.to_csv(index=False), encoding="utf-8")

    merged = read_silver_dataset(silver_dir)
    assert len(merged) == 1

    sqlite_path = tmp_path / "gold" / "air_quality.db"
    inserted_first = load_to_sqlite(merged, sqlite_path)
    inserted_second = load_to_sqlite(merged, sqlite_path)

    assert inserted_first == 1
    assert inserted_second == 0
