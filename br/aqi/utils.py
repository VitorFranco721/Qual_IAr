"""Funções utilitárias compartilhadas pelo pipeline.

Centraliza rotinas comuns como parsing de data e tratamento de timezone para
evitar duplicação de código e facilitar manutenção.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Union

from dateutil import tz

LOCAL_TZ = tz.gettz("America/Sao_Paulo")


def parse_date(value: str) -> date:
    """Converte uma string para `date`.

    Aceita datas ISO (`YYYY-MM-DD`) e a palavra `today`.
    """
    if value.lower() == "today":
        return datetime.now(tz=LOCAL_TZ).date()
    return datetime.strptime(value, "%Y-%m-%d").date()


def ensure_datetime(value: Union[str, datetime]) -> datetime:
    """Garante que `value` seja `datetime` com timezone."""
    import pandas as pd

    if isinstance(value, datetime):
        dt = value
    else:
        dt = pd.to_datetime(value).to_pydatetime()
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=LOCAL_TZ)
    return dt


def to_utc(dt: datetime) -> datetime:
    """Converte um `datetime` para UTC."""
    return dt.astimezone(timezone.utc)