"""GEO-SEO Suite CLI - Command-line interface for GEO/SEO analysis."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Annotated

import typer
from rich.console import Console
from rich.panel import Panel

from geo_seo import __version__

if TYPE_CHECKING:
    pass

app = typer.Typer(
    name="geo-seo",
    help="GEO-SEO Suite v2.0 - Professional GEO/SEO optimization toolkit.",
    add_completion=False,
    rich_markup_mode="rich",
)
console = Console()


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(
            f"[bold green]geo-seo-suite[/] version [bold]{__version__}[/]"
        )
        raise typer.Exit


@app.callback()
def main(
    version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            "-v",
            help="Show version and exit.",
            callback=version_callback,
            is_eager=True,
        ),
    ] = None,
) -> None:
    """GEO-SEO Suite v2.0 - Optimize your content for AI search engines and LLMs."""


@app.command()
def analyze(
    url: Annotated[str, typer.Argument(help="URL to analyze")],
    config: Annotated[
        Path | None,
        typer.Option("--config", "-c", help="Path to config YAML file"),
    ] = None,
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Output file path"),
    ] = None,
    fmt: Annotated[
        str,
        typer.Option("--format", "-f", help="Output format: json, pdf, html"),
    ] = "json",
) -> None:
    """Analyze a URL for GEO/SEO scoring across 24+ metrics."""
    console.print(
        Panel(
            f"[bold]Analyzing:[/] {url}\n"
            f"[dim]Format: {fmt} | Config: {config or 'default'}[/]",
            title="[bold blue]GEO-SEO Analysis[/]",
            border_style="blue",
        )
    )
    console.print("[yellow]Scoring engine will be available in Phase 1.[/]")


@app.command()
def monitor(
    url: Annotated[str, typer.Argument(help="URL to monitor")],
    config: Annotated[
        Path | None,
        typer.Option("--config", "-c", help="Path to config YAML file"),
    ] = None,
    days: Annotated[
        int,
        typer.Option("--days", "-d", help="Number of days to look back"),
    ] = 30,
) -> None:
    """Monitor temporal changes in GEO/SEO metrics for a URL."""
    console.print(
        Panel(
            f"[bold]Monitoring:[/] {url}\n"
            f"[dim]Period: {days} days | Config: {config or 'default'}[/]",
            title="[bold blue]GEO-SEO Monitor[/]",
            border_style="blue",
        )
    )
    console.print(
        "[yellow]Monitoring system will be available in Phase 2.[/]"
    )


@app.command()
def generate(
    url: Annotated[
        str, typer.Argument(help="URL to generate optimizations for")
    ],
    config: Annotated[
        Path | None,
        typer.Option("--config", "-c", help="Path to config YAML file"),
    ] = None,
    output_dir: Annotated[
        Path | None,
        typer.Option("--output-dir", "-o", help="Output directory"),
    ] = None,
) -> None:
    """Generate llms.txt and optimized Schema.org markup for a URL."""
    console.print(
        Panel(
            f"[bold]Generating for:[/] {url}\n"
            f"[dim]Output: {output_dir or './output'} "
            f"| Config: {config or 'default'}[/]",
            title="[bold blue]GEO-SEO Generator[/]",
            border_style="blue",
        )
    )
    console.print(
        "[yellow]Generation engine will be available in Phase 3.[/]"
    )


@app.command()
def compare(
    urls: Annotated[
        list[str],
        typer.Argument(help="URLs to compare (space-separated)"),
    ],
    config: Annotated[
        Path | None,
        typer.Option("--config", "-c", help="Path to config YAML file"),
    ] = None,
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Output file path"),
    ] = None,
) -> None:
    """Compare GEO/SEO scores across multiple URLs."""
    console.print(
        Panel(
            f"[bold]Comparing {len(urls)} URLs[/]\n"
            + "\n".join(f"  - {u}" for u in urls),
            title="[bold blue]GEO-SEO Compare[/]",
            border_style="blue",
        )
    )
    console.print(
        "[yellow]Comparison engine will be available in Phase 1.[/]"
    )


@app.command()
def serve(
    host: Annotated[
        str, typer.Option("--host", "-h", help="API server host")
    ] = "0.0.0.0",
    port: Annotated[
        int, typer.Option("--port", "-p", help="API server port")
    ] = 8000,
    config: Annotated[
        Path | None,
        typer.Option("--config", "-c", help="Path to config YAML file"),
    ] = None,
) -> None:
    """Start the GEO-SEO API server."""
    console.print(
        Panel(
            f"[bold]Server:[/] {host}:{port}\n"
            f"[dim]Config: {config or 'default'}[/]",
            title="[bold blue]GEO-SEO API Server[/]",
            border_style="blue",
        )
    )
    console.print(
        "[yellow]API server will be available in Phase 4.[/]"
    )


@app.command("config-init")
def config_init(
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output path for config file"),
    ] = Path("geo-seo.yaml"),
) -> None:
    """Generate a template configuration file."""
    template = """# GEO-SEO Suite v2.0 Configuration
# See docs for full reference: https://github.com/vanesarossi61/geo-seo-suite

general:
  output_format: json  # json, pdf, html
  output_dir: ./output
  verbose: false
  language: auto  # auto, en, es, fr, de, pt, it

scoring:
  preset: general  # general, ecommerce, saas, blog, news
  weights: {}  # Override individual metric weights

crawling:
  timeout: 30
  max_retries: 3
  user_agent: "GEO-SEO-Suite/2.0"
  render_js: false

monitoring:
  check_interval: 24h
  retention_days: 90

database:
  path: ./geo-seo.db
  echo: false
"""
    output.write_text(template)
    console.print(f"[bold green]Config template written to:[/] {output}")
    console.print("[dim]Edit the file to customize your settings.[/]")


if __name__ == "__main__":
    app()
