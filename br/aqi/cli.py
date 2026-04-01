"""Interface de linha de comando (CLI) do projeto.

Este módulo concentra os comandos do pipeline de dados em uma interface única.
Cada comando executa uma etapa do fluxo medalhão:

- descoberta de fontes
- extração de dados brutos (Bronze)
- normalização (Silver)
- validação
- exportação
- carga em banco (Gold/Serving)

Os comandos foram projetados para serem idempotentes, ou seja: podem ser
executados novamente sem corromper o histórico já processado.
"""
from __future__ import annotations

import asyncio
import json
import os
from datetime import date, datetime
from pathlib import Path
from typing import Optional

import typer

from .rag import crawl_candidates, rank_sources, plan_per_source
from .sources import get_sources
from .normalize import normalize_dataframe
from .validate import validate_dataframe
from .export import export_to_csv
from .load import read_silver_dataset, load_to_sqlite, load_to_mongo
from .utils import parse_date


app = typer.Typer(add_completion=False, help="Pipeline de qualidade do ar de Brasília")


@app.command()
def discover() -> None:
    """Descobre fontes candidatas e salva o índice ranqueado em artefatos."""

    async def _run() -> None:
        candidates = await crawl_candidates()
        ranked = rank_sources(candidates)
        # Salva índice de fontes em artifacts.
        artifacts_dir = Path("artifacts")
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        index_path = artifacts_dir / "sources_index.json"
        with index_path.open("w", encoding="utf-8") as fh:
            json.dump(ranked, fh, indent=2, ensure_ascii=False)
        typer.echo(f"{len(ranked)} fontes salvas em {index_path}")

    asyncio.run(_run())


@app.command()
def extract(
    since: str = typer.Option(
        "2020-01-01",
        help="Data inicial (formato ISO) para extração",
        show_default=True,
    ),
    until: str = typer.Option(
        "today",
        help="Data final (formato ISO); use 'today' para hoje",
        show_default=True,
    ),
) -> None:
    """Baixa dados brutos de todas as fontes configuradas para a camada Bronze."""
    start = parse_date(since)
    end = parse_date(until)
    if end < start:
        raise typer.BadParameter("A data final deve ser igual ou maior que a data inicial")

    # Garante diretórios necessários.
    data_dir = Path("data/bronze")
    data_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = Path("artifacts/cache")
    cache_dir.mkdir(parents=True, exist_ok=True)

    async def _run() -> None:
        sources = get_sources()
        tasks = []
        for source in sources:
            tasks.append(source.extract(start, end, cache_dir, data_dir))
        await asyncio.gather(*tasks)
        typer.echo(f"Extração concluída para {len(tasks)} fonte(s)")

    asyncio.run(_run())


@app.command()
def normalize() -> None:
    """Normaliza os dados brutos e grava o resultado na camada Silver."""
    import pandas as pd

    bronze_dir = Path("data/bronze")
    silver_dir = Path("data/silver")
    silver_dir.mkdir(parents=True, exist_ok=True)
    for raw_file in bronze_dir.glob("*.csv"):
        df = pd.read_csv(raw_file)
        norm = normalize_dataframe(df)
        out_path = silver_dir / raw_file.name
        norm.to_csv(out_path, index=False)
        typer.echo(f"Normalizado: {raw_file} -> {out_path}")


@app.command()
def validate() -> None:
    """Valida os dados normalizados e informa inconsistências encontradas."""
    import pandas as pd
    from rich import print as rprint

    silver_dir = Path("data/silver")
    success = True
    for file in silver_dir.glob("*.csv"):
        df = pd.read_csv(file)
        report = validate_dataframe(df)
        if report:
            success = False
            rprint(f"[bold red]Problemas de validação em {file}:[/bold red]")
            for issue in report:
                rprint(f" - {issue}")
    if not success:
        raise typer.Exit(code=1)
    typer.echo("Todos os arquivos passaram na validação")


@app.command()
def export(format: str = typer.Option("csv", help="Formato de saída: csv ou parquet")) -> None:
    """Exporta dados normalizados para o formato escolhido."""
    import pandas as pd

    silver_dir = Path("data/silver")
    export_dir = Path("data/export")
    export_dir.mkdir(parents=True, exist_ok=True)
    for file in silver_dir.glob("*.csv"):
        df = pd.read_csv(file)
        export_to_csv(df, export_dir)
        if format.lower() == "parquet":
            try:
                import pyarrow  # noqa: F401
                pq_path = export_dir / (file.stem + ".parquet")
                df.to_parquet(pq_path)
                typer.echo(f"Arquivo gerado: {pq_path}")
            except ImportError:
                typer.echo("pyarrow não está instalado; exportação Parquet ignorada", err=True)
    typer.echo("Exportação concluída")


@app.command()
def load(
    sqlite_path: str = typer.Option(
        "data/gold/air_quality.db",
        help="Caminho do SQLite para a camada Gold/Serving",
        show_default=True,
    ),
    mongo_uri: Optional[str] = typer.Option(
        None,
        help="URI de conexão do MongoDB; se vazio, usa AQI_MONGO_URI",
    ),
    mongo_database: str = typer.Option(
        "air_quality",
        help="Nome do banco no MongoDB",
        show_default=True,
    ),
    mongo_collection: str = typer.Option(
        "measurements",
        help="Nome da coleção no MongoDB",
        show_default=True,
    ),
) -> None:
    """Carrega a camada Silver em SQLite e, opcionalmente, MongoDB."""
    silver_dir = Path("data/silver")
    if not silver_dir.exists():
        raise typer.BadParameter("Diretório data/silver não encontrado; execute normalize antes")

    df = read_silver_dataset(silver_dir)
    if df.empty:
        typer.echo("Não há dados Silver para carregar")
        return

    changed = load_to_sqlite(df, Path(sqlite_path))
    typer.echo(f"SQLite: {changed} nova(s) linha(s) carregada(s)")

    final_mongo_uri = mongo_uri or os.getenv("AQI_MONGO_URI")
    if final_mongo_uri:
        inserted = load_to_mongo(
            df,
            mongo_uri=final_mongo_uri,
            database=mongo_database,
            collection=mongo_collection,
        )
        typer.echo(f"MongoDB: {inserted} novo(s) documento(s) carregado(s)")
    else:
        typer.echo("Carga em MongoDB ignorada (AQI_MONGO_URI não definida)")


if __name__ == "__main__":  # pragma: no cover
    app()