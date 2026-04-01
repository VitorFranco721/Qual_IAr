"""Funções de descoberta e ranqueamento de fontes (RAG simplificado).

O objetivo deste módulo é montar uma lista de fontes oficiais de dados,
atribuir pontuação de relevância e definir um plano de extração por fonte.

Nesta versão, a descoberta é determinística (fontes conhecidas) para manter
reprodutibilidade e simplicidade.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

import structlog


logger = structlog.get_logger(__name__)


@dataclass
class SourceCandidate:
    """Representa uma fonte descoberta e seus metadados de avaliação."""

    id: str
    title: str
    url: str
    agency: str
    format: str
    score: float
    metadata: Dict[str, Any]


async def crawl_candidates() -> List[Dict[str, Any]]:
    """Retorna lista de fontes candidatas para qualidade do ar no DF.

    Nesta implementação, a lista é fixa e baseada em fontes públicas oficiais.
    """
    # Fontes predefinidas com base em documentação oficial.
    candidates: List[Dict[str, Any]] = [
        {
            "id": "arcgis_stations",
            "title": "Estações de monitoramento da qualidade do ar (licenciamento)",
            "url": "https://onda.ibram.df.gov.br/server/rest/services/Hosted/Estações_de_monitoramento_da_qualidade_do_ar_estabelecidas_por_licenciamento_ambiental/FeatureServer/0",
            "agency": "IBRAM",
            "format": "ArcGIS FeatureLayer",
            "metadata": {
                "record_count": 9,
                "supported_formats": ["csv", "geojson"],
            },
        },
        {
            "id": "monitorar",
            "title": "MonitorAr (dados em tempo real das estações automáticas)",
            "url": "https://monitorar.mma.gov.br",
            "agency": "MMA",
            "format": "Web service",
            "metadata": {
                "description": "Dados em tempo real de AQI e concentração de poluentes",
            },
        },
    ]
    logger.info("Descoberta concluída", count=len(candidates))
    return candidates


def rank_sources(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Classifica fontes por oficialidade, formato e cobertura.

    A pontuação é uma heurística simples, suficiente para priorizar
    automaticamente as fontes mais confiáveis.
    """
    ranked: List[Dict[str, Any]] = []
    for cand in candidates:
        score = 0.0
        # Oficialidade: fontes governamentais ganham peso maior.
        if cand["agency"].lower() in {"ibram", "mma", "mma"}:
            score += 0.5
        # Formato: APIs abertas/CSV/JSON recebem bônus.
        fmt = cand.get("format", "").lower()
        if any(f in fmt for f in ["csv", "json", "featurelayer"]):
            score += 0.3
        # Cobertura: presença de volume conhecido aumenta confiança.
        meta = cand.get("metadata", {})
        if meta.get("record_count", 0) > 0:
            score += 0.2
        cand["score"] = score
        ranked.append(cand)
    ranked.sort(key=lambda c: c["score"], reverse=True)
    return ranked


def plan_per_source(source: Dict[str, Any]) -> Dict[str, Any]:
    """Gera um plano de extração para uma fonte específica."""
    if source["id"] == "arcgis_stations":
        return {
            "type": "arcgis_feature_layer",
            "layer_url": source["url"],
            "pagination": False,
            "description": "Buscar metadados das estações pela API REST do ArcGIS."
        }
    if source["id"] == "monitorar":
        return {
            "type": "monitorar_api",
            "base_url": source["url"],
            "description": "Consumir MonitorAr (API/scraping) para medições em tempo real."
        }
    return {"type": "unknown"}