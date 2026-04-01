"""Carga da camada Silver para repositórios de consumo (Gold/Serving).

Este módulo separa a responsabilidade de carga em banco do restante do ETL.
Suporta escrita incremental em:

- SQLite (disponível por padrão no Python)
- MongoDB (opcional)
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

import pandas as pd

CANONICAL_COLUMNS = [
    "datetime_utc",
    "datetime_local",
    "station_id",
    "station_name",
    "latitude",
    "longitude",
    "pollutant",
    "value",
    "unit",
    "avg_period_minutes",
    "source_url",
    "source_agency",
    "ingested_at_utc",
    "license",
    "quality_flag",
]


def read_silver_dataset(silver_dir: Path) -> pd.DataFrame:
    """Lê e concatena todos os CSVs da camada Silver."""
    files = sorted(silver_dir.glob("*.csv"))
    if not files:
        return pd.DataFrame(columns=CANONICAL_COLUMNS)

    frames = [pd.read_csv(file) for file in files]
    merged = pd.concat(frames, ignore_index=True)
    for col in CANONICAL_COLUMNS:
        if col not in merged.columns:
            merged[col] = None
    return merged[CANONICAL_COLUMNS]


def load_to_sqlite(df: pd.DataFrame, sqlite_path: Path) -> int:
    """Carrega linhas canônicas em SQLite com deduplicação por chave única."""
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(sqlite_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS air_quality_measurements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                datetime_utc TEXT,
                datetime_local TEXT,
                station_id TEXT,
                station_name TEXT,
                latitude REAL,
                longitude REAL,
                pollutant TEXT,
                value REAL,
                unit TEXT,
                avg_period_minutes INTEGER,
                source_url TEXT,
                source_agency TEXT,
                ingested_at_utc TEXT,
                license TEXT,
                quality_flag TEXT,
                UNIQUE(datetime_utc, station_id, pollutant, source_agency)
            )
            """
        )

        payload = [
            (
                row["datetime_utc"],
                row["datetime_local"],
                row["station_id"],
                row["station_name"],
                row["latitude"],
                row["longitude"],
                row["pollutant"],
                row["value"],
                row["unit"],
                row["avg_period_minutes"],
                row["source_url"],
                row["source_agency"],
                row["ingested_at_utc"],
                row["license"],
                row["quality_flag"],
            )
            for _, row in df.iterrows()
        ]

        conn.executemany(
            """
            INSERT OR IGNORE INTO air_quality_measurements (
                datetime_utc,
                datetime_local,
                station_id,
                station_name,
                latitude,
                longitude,
                pollutant,
                value,
                unit,
                avg_period_minutes,
                source_url,
                source_agency,
                ingested_at_utc,
                license,
                quality_flag
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            payload,
        )
        conn.commit()
        return conn.total_changes


def load_to_mongo(
    df: pd.DataFrame,
    mongo_uri: str,
    database: str = "air_quality",
    collection: str = "measurements",
) -> int:
    """Carrega linhas canônicas no MongoDB e ignora duplicados."""
    try:
        from pymongo import MongoClient
        from pymongo.errors import BulkWriteError
    except ImportError as exc:  # pragma: no cover - depends on optional package
        raise RuntimeError(
            "pymongo não instalado. Instale com: pip install pymongo"
        ) from exc

    client = MongoClient(mongo_uri)
    coll = client[database][collection]
    coll.create_index(
        [
            ("datetime_utc", 1),
            ("station_id", 1),
            ("pollutant", 1),
            ("source_agency", 1),
        ],
        unique=True,
    )

    docs = df.to_dict(orient="records")
    if not docs:
        return 0

    inserted = 0
    try:
        result = coll.insert_many(docs, ordered=False)
        inserted = len(result.inserted_ids)
    except BulkWriteError as err:
        inserted = err.details.get("nInserted", 0)
    finally:
        client.close()

    return inserted
