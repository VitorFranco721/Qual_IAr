"""Regras de validação para dados normalizados de qualidade do ar.

A validação garante que a camada Silver tenha consistência mínima antes de
seguir para exportação e carga em banco.
"""
from __future__ import annotations

from datetime import datetime
from typing import List

import pandas as pd


RANGES = {
    "pm25": (0, 1000),
    "pm10": (0, 1000),
    "o3": (0, 200),
    "no2": (0, 400),
    "so2": (0, 400),
    "co": (0, 10000),
}


def validate_dataframe(df: pd.DataFrame) -> List[str]:
    """Valida um dataframe e retorna lista de problemas encontrados.

    Lista vazia significa que os dados passaram em todas as regras.
    """
    issues: List[str] = []
    # Verifica faixas plausíveis de concentração por poluente.
    for idx, row in df.iterrows():
        pollutant = row.get("pollutant")
        value = row.get("value")
        if pd.isna(value):
            continue
        try:
            val = float(value)
        except (TypeError, ValueError):
            issues.append(f"Linha {idx}: valor '{value}' não é numérico")
            continue
        if pollutant in RANGES:
            lo, hi = RANGES[pollutant]
            if not (lo <= val <= hi):
                issues.append(
                    f"Linha {idx}: concentração de {pollutant} ({val}) fora da faixa [{lo}, {hi}]"
                )
    # Verifica ordenação temporal (não decrescente).
    try:
        dt_series = pd.to_datetime(df["datetime_utc"])
        if not dt_series.is_monotonic_increasing:
            issues.append("Timestamps não estão em ordem não decrescente")
    except Exception:
        issues.append("Valores inválidos em datetime_utc")
    # Verifica se coordenadas estão dentro dos limites aproximados do Brasil.
    for idx, row in df.iterrows():
        lat, lon = row.get("latitude"), row.get("longitude")
        try:
            if pd.notna(lat) and pd.notna(lon):
                if not (-33 <= float(lat) <= 5 and -74 <= float(lon) <= -34):
                    issues.append(
                        f"Linha {idx}: coordenadas ({lat}, {lon}) fora dos limites do Brasil"
                    )
        except Exception:
            issues.append(f"Linha {idx}: coordenadas inválidas ({lat}, {lon})")
    # Verifica colunas obrigatórias.
    required = {
        "datetime_utc",
        "datetime_local",
        "station_id",
        "station_name",
        "pollutant",
        "value",
        "unit",
        "avg_period_minutes",
        "source_url",
        "source_agency",
        "ingested_at_utc",
        "quality_flag",
    }
    missing = required - set(df.columns)
    if missing:
        issues.append(f"Colunas obrigatórias ausentes: {', '.join(sorted(missing))}")
    return issues