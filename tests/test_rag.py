import pytest

from br.aqi.rag import rank_sources


def test_rank_sources_orders_by_score() -> None:
    """Valida que a fonte mais oficial/aberta recebe maior pontuação."""
    candidates = [
        {
            "id": "s1",
            "agency": "IBRAM",
            "format": "csv",
            "metadata": {"record_count": 10},
        },
        {
            "id": "s2",
            "agency": "Other",
            "format": "json",
            "metadata": {},
        },
    ]
    ranked = rank_sources(candidates)
    assert ranked[0]["id"] == "s1"
    assert ranked[0]["score"] >= ranked[1]["score"]