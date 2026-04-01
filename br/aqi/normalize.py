"""Normalização dos dados brutos de qualidade do ar.

Este módulo converte dataframes de entrada para o esquema canônico da camada
Silver. A etapa de normalização padroniza:

- nomes de poluentes
- unidades de medida
- timezone e formato dos timestamps
- metadados obrigatórios
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

import pandas as pd
from dateutil import tz

LOCAL_TZ = tz.gettz("America/Sao_Paulo")


POLLUTANT_MAP = {
    "pm25": "pm25",
    "pm2.5": "pm25",
    "mp2,5": "pm25",
    "pm10": "pm10",
    "mp10": "pm10",
    "o3": "o3",
    "ozone": "o3",
    "no2": "no2",
    "so2": "so2",
    "co": "co",
}


def convert_unit(value: float, unit: str) -> float:
    """Converte concentração para µg/m³ quando necessário.

    Atualmente apenas CO pode vir em mg/m³. Nesses casos, multiplica por 1000.
    """
    unit = unit.lower() if isinstance(unit, str) else ""
    if unit in {"mg/m³", "mg/m3", "mg/m^3"}:
        return value * 1000
    return value


def normalize_datetime(ts: str) -> tuple[str, str]:
    """Retorna `(datetime_utc_iso, datetime_local_iso)` para um timestamp."""
    dt = pd.to_datetime(ts)
    if dt.tzinfo is None:
        # Assume horário local quando vier sem timezone.
        local_dt = dt.replace(tzinfo=LOCAL_TZ)
    else:
        local_dt = dt.astimezone(LOCAL_TZ)
    utc_dt = local_dt.astimezone(timezone.utc)
    return utc_dt.isoformat(), local_dt.isoformat()


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza um dataframe bruto para o esquema canônico Silver.

    Mesmo que a origem tenha colunas incompletas, o método tenta preencher
    padrões mínimos para manter o pipeline estável.
    """
    records = []
    for _, row in df.iterrows():
        pollutant_raw = str(row.get("pollutant")).lower()
        pollutant = POLLUTANT_MAP.get(pollutant_raw, pollutant_raw)
        value = row.get("value")
        unit = row.get("unit") or "µg/m³"
        if pd.notna(value):
            value = float(value)
            value = convert_unit(value, unit)
        dt_utc_iso, dt_local_iso = normalize_datetime(row.get("datetime_utc") or row.get("datetime_local"))
        records.append(
            {
                "datetime_utc": dt_utc_iso,
                "datetime_local": dt_local_iso,
                "station_id": row.get("station_id"),
                "station_name": row.get("station_name"),
                "latitude": row.get("latitude"),
                "longitude": row.get("longitude"),
                "pollutant": pollutant,
                "value": value,
                "unit": "µg/m³",
                "avg_period_minutes": int(row.get("avg_period_minutes") or 60),
                "source_url": row.get("source_url"),
                "source_agency": row.get("source_agency"),
                "ingested_at_utc": row.get("ingested_at_utc") or datetime.now(timezone.utc).isoformat(),
                "license": row.get("license"),
                "quality_flag": row.get("quality_flag") or "ok",
            }
        )
    return pd.DataFrame(records)