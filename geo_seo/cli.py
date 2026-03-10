"""GEO-SEO Suite CLI -- command-line interface powered by Typer."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.panel import Panel

from geo_seo import __version__

# ---------------------------------------------------------------------------
# App & console
# ---------------------------------------------------------------------------

console = Console()

app = typer.Typer(
    name="geo-seo",
    help="GEO-SEO Suite v2.0 -- Professional GEO/SEO analysis toolkit.",
    add_completion=False,
    rich_markup_mode="rich",
)


# ---------------------------------------------------------------------------
# Version callback
# ---------------------------------------------------------------------------


def _version_callback(value: bool) -> None:  # noqa: FBT001
    """Print version and exit."""
    if value:
        console.print(f"geo-seo-suite [bold cyan]{__version__}[/bold cyan]")
        raise typer.Exit


@app.callback()
def main(
    version: Annotated[
        Optional[bool],
        typer.Option(
            "--version",
            "-V",
            help="Show the version and exit.",
            callback=_version_callback,
            is_eager=True,
        ),
    ] = None,
) -> None:
    """GEO-SEO Suite -- analyse, score, and optimise content for generative engines."""


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@app.command()
def analyze(
    url: Annotated[str, typer.Argument(help="URL to analyse for GEO/SEO scoring.")],
    config: Annotated[
        Optional[Path],
        typer.Option("--config", "-c", help="Path to YAML configuration file."),
    ] = None,
    output: Annotated[
        Optional[Path],
        typer.Option("--output", "-o", help="Path to save the analysis report."),
    ] = None,
    fmt: Annotated[
        str,
        typer.Option("--format", "-f", help="Output format: json, csv, html, markdown."),
    ] = "json",
) -> None:
    """Analyse a URL for GEO/SEO scoring.

    Runs the full scoring pipeline on the given URL and produces a detailed
    report covering content quality, structured data, LLM readability, and
    brand consistency.
    """
    console.print(
        Panel(
            f"[bold]Analyse[/bold] command received for [cyan]{url}[/cyan]\n"
            f"Config: {config or 'default'} | Format: {fmt} | Output: {output or 'stdout'}\n\n"
            "[yellow]Module will be implemented in Phase 0.3+ (core extraction & scoring).[/yellow]",
            title="geo-seo analyze",
            border_style="blue",
        )
    )


@app.command()
def monitor(
    url: Annotated[str, typer.Argument(help="URL to monitor over time.")],
    config: Annotated[
        Optional[Path],
        typer.Option("--config", "-c", help="Path to YAML configuration file."),
    ] = None,
    days: Annotated[
        int,
        typer.Option("--days", "-d", help="Number of days to look back."),
    ] = 30,
) -> None:
    """Monitor temporal changes for a URL.

    Tracks score evolution, content changes, and structured-data updates
    over the specified time window.
    """
    console.print(
        Panel(
            f"[bold]Monitor[/bold] command received for [cyan]{url}[/cyan]\n"
            f"Config: {config or 'default'} | Days: {days}\n\n"
            "[yellow]Module will be implemented in Phase 2 (monitoring subsystem).[/yellow]",
            title="geo-seo monitor",
            border_style="blue",
        )
    )


@app.command()
def generate(
    url: Annotated[str, typer.Argument(help="URL to generate optimised assets for.")],
    config: Annotated[
        Optional[Path],
        typer.Option("--config", "-c", help="Path to YAML configuration file."),
    ] = None,
    output_dir: Annotated[
        Path,
        typer.Option("--output-dir", "-o", help="Directory to write generated files."),
    ] = Path("output"),
) -> None:
    """Generate llms.txt and schema.org optimised markup.

    Produces machine-readable artefacts (llms.txt, JSON-LD schemas) that
    improve discoverability by large-language-model-powered search engines.
    """
    console.print(
        Panel(
            f"[bold]Generate[/bold] command received for [cyan]{url}[/cyan]\n"
            f"Config: {config or 'default'} | Output dir: {output_dir}\n\n"
            "[yellow]Module will be implemented in Phase 1 (generation subsystem).[/yellow]",
            title="geo-seo generate",
            border_style="blue",
        )
    )


@app.command()
def compare(
    urls: Annotated[
        list[str],
        typer.Argument(help="Two or more URLs to compare."),
    ],
    config: Annotated[
        Optional[Path],
        typer.Option("--config", "-c", help="Path to YAML configuration file."),
    ] = None,
    output: Annotated[
        Optional[Path],
        typer.Option("--output", "-o", help="Path to save the comparison report."),
    ] = None,
) -> None:
    """Compare multiple URLs side by side.

    Generates a comparative analysis including score deltas, content
    structure differences, and competitive positioning insights.
    """
    urls_display = ", ".join(urls)
    console.print(
        Panel(
            f"[bold]Compare[/bold] command received for [cyan]{urls_display}[/cyan]\n"
            f"Config: {config or 'default'} | Output: {output or 'stdout'}\n\n"
            "[yellow]Module will be implemented in Phase 1 (comparison engine).[/yellow]",
            title="geo-seo compare",
            border_style="blue",
        )
    )


@app.command()
def serve(
    host: Annotated[
        str,
        typer.Option("--host", "-h", help="Bind address."),
    ] = "127.0.0.1",
    port: Annotated[
        int,
        typer.Option("--port", "-p", help="Port number."),
    ] = 8000,
    config: Annotated[
        Optional[Path],
        typer.Option("--config", "-c", help="Path to YAML configuration file."),
    ] = None,
) -> None:
    """Start the GEO-SEO API server.

    Launches a FastAPI-based HTTP server exposing the full scoring and
    generation pipeline via REST endpoints.
    """
    console.print(
        Panel(
            f"[bold]Serve[/bold] command: API server at [cyan]{host}:{port}[/cyan]\n"
            f"Config: {config or 'default'}\n\n"
            "[yellow]Module will be implemented in Phase 3 (API layer).[/yellow]",
            title="geo-seo serve",
            border_style="blue",
        )
    )


@app.command("config-init")
def config_init(
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Path for the generated config file."),
    ] = Path("geo-seo.yaml"),
) -> None:
    """Generate a template configuration file.

    Writes a fully-commented YAML configuration file with sensible defaults
    that can be customised for your specific analysis needs.
    """
    template = (
        "# GEO-SEO Suite configuration\n"
        "# Generated by geo-seo config-init\n"
        "#\n"
        "# Docs: https://github.com/vanesarossi61/geo-seo-suite#readme\n"
        "\n"
        "general:\n"
        "  language: es\n"
        "  output_format: json\n"
        "  log_level: INFO\n"
        "\n"
        "scoring:\n"
        "  weights:\n"
        "    content_quality: 0.25\n"
        "    structured_data: 0.20\n"
        "    llm_readability: 0.20\n"
        "    brand_consistency: 0.15\n"
        "    technical_seo: 0.20\n"
        "\n"
        "crawling:\n"
        "  timeout: 30\n"
        "  max_retries: 3\n"
        "  user_agent: geo-seo-suite/2.0\n"
        "  respect_robots_txt: true\n"
        "\n"
        "monitoring:\n"
        "  check_interval_hours: 24\n"
        "  retention_days: 90\n"
        "\n"
        "database:\n"
        "  path: geo-seo.db\n"
    )
    output.write_text(template, encoding="utf-8")
    console.print(
        Panel(
            f"Configuration template written to [green]{output}[/green]\n\n"
            "Edit the file to customise scoring weights, crawling behaviour,\n"
            "and monitoring settings for your project.",
            title="geo-seo config-init",
            border_style="green",
        )
    )
