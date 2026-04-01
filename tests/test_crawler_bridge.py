import asyncio
from datetime import date
from pathlib import Path

import pandas as pd

from br.aqi.sources import IQAirCrawlerOutputSource


def test_iqair_crawler_source_extracts_to_bronze(tmp_path: Path) -> None:
    crawler_output = tmp_path / "crawler_output"
    crawler_output.mkdir()

    raw = pd.DataFrame(
        [
            {
                "id": 1,
                "city": "Brasília",
                "country": "Brasil",
                "aqi": 55,
                "pm25": 15.1,
                "pm10": 30.2,
                "created_at": "2026-03-01T12:00:00",
            }
        ]
    )
    raw.to_csv(crawler_output / "iqair_data_test.csv", index=False)

    bronze_dir = tmp_path / "bronze"
    bronze_dir.mkdir()
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()

    source = IQAirCrawlerOutputSource(crawler_output_dir=crawler_output)
    asyncio.run(source.extract(date(2026, 3, 1), date(2026, 3, 2), cache_dir, bronze_dir))

    out_file = bronze_dir / "iqair_crawler.csv"
    assert out_file.exists()

    bronze = pd.read_csv(out_file)
    assert {"pm25", "pm10"}.issubset(set(bronze["pollutant"]))
    assert len(bronze) == 2
