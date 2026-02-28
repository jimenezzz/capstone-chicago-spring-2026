from pathlib import Path

import typer

from pipelines.ingestion.sources.cms_asp_pricing import ingest_cms_asp_pricing
from pipelines.ingestion.sources.cms_crosswalk import ingest_cms_crosswalk
from pipelines.ingestion.sources.nadac import ingest_nadac
from pipelines.ingestion.sources.openfda import ingest_openfda
from pipelines.ingestion.sources.orange_book import ingest_orange_book
from pipelines.ingestion.sources.purple_book import ingest_purple_book
from pipelines.ingestion.utils import parse_as_of
from shared.db.session import get_session_factory

app = typer.Typer(help="Ingestion CLI for Pharmaceutical Economic Data Hub")


def _run_ingestion(fn, *args, **kwargs):
    session_factory = get_session_factory()
    session = session_factory()
    try:
        result = fn(session, *args, **kwargs)
        session.commit()
        typer.echo(result)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@app.command("nadac")
def cmd_nadac(
    path: str = typer.Option(..., "--path", help="Path to NADAC csv/xlsx file"),
    as_of: str = typer.Option(..., "--as-of", help="Historical as-of date YYYY-MM-DD"),
    force: bool = typer.Option(False, "--force", help="Re-ingest even if hash exists"),
):
    _run_ingestion(ingest_nadac, path, parse_as_of(as_of), force=force)


@app.command("orange-book")
def cmd_orange_book(
    zip_path: str = typer.Option(..., "--zip", help="Path to Orange Book extracted dir or products.txt"),
    as_of: str = typer.Option(..., "--as-of", help="Historical as-of date YYYY-MM-DD"),
    force: bool = typer.Option(False, "--force"),
):
    _run_ingestion(ingest_orange_book, zip_path, parse_as_of(as_of), force=force)


@app.command("purple-book")
def cmd_purple_book(
    path: str = typer.Option(..., "--path", help="Path to Purple Book file"),
    as_of: str = typer.Option(..., "--as-of"),
    force: bool = typer.Option(False, "--force"),
):
    _run_ingestion(ingest_purple_book, path, parse_as_of(as_of), force=force)


@app.command("openfda")
def cmd_openfda(
    as_of: str = typer.Option(..., "--as-of"),
    ndc_file: str | None = typer.Option(None, "--ndc-file", help="File containing ndc list"),
    ndc_list: str | None = typer.Option(None, "--ndc-list", help="Comma separated ndc values"),
    local_json: str | None = typer.Option(None, "--local-json", help="Local OpenFDA NDC JSON"),
    force: bool = typer.Option(False, "--force"),
):
    _run_ingestion(
        ingest_openfda,
        parse_as_of(as_of),
        ndc_file=ndc_file,
        ndc_list=ndc_list,
        local_json=local_json,
        force=force,
    )


@app.command("cms-crosswalk")
def cmd_cms_crosswalk(
    dir: str = typer.Option(..., "--dir", help="Directory with CMS crosswalk CSV files"),
    as_of: str = typer.Option(..., "--as-of"),
    force: bool = typer.Option(False, "--force"),
):
    _run_ingestion(ingest_cms_crosswalk, dir, parse_as_of(as_of), force=force)


@app.command("cms-asp")
def cmd_cms_asp(
    dir: str = typer.Option(..., "--dir", help="Directory or file for CMS ASP pricing"),
    as_of: str = typer.Option(..., "--as-of"),
    force: bool = typer.Option(False, "--force"),
):
    _run_ingestion(ingest_cms_asp_pricing, dir, parse_as_of(as_of), force=force)


if __name__ == "__main__":
    app()
