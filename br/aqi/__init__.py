"""Pacote principal do projeto `brasilia_air_quality`.

Este pacote oferece ferramentas para descobrir, extrair, normalizar, validar,
exportar e carregar dados de qualidade do ar do Distrito Federal.

O ponto de entrada principal para uso diário é a CLI em `br/aqi/cli.py`.
"""

from importlib.metadata import version as _get_version


def __getattr__(name: str):  # pragma: no cover
    if name == "__version__":
        return _get_version("brasilia-air-quality")
    raise AttributeError(name)


__all__ = ["cli", "rag", "sources", "normalize", "validate", "export", "utils"]