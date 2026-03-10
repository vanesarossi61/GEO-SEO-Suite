"""Unit tests for the GEO-SEO Suite CLI."""

from __future__ import annotations

from typer.testing import CliRunner

from geo_seo import __version__
from geo_seo.cli import app

runner = CliRunner()


def test_version() -> None:
    """--version flag prints the current version string."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output
    assert "2.0.0" in result.output


def test_help() -> None:
    """--help lists all registered commands."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    # Every command name must appear in the help output
    for cmd in ("analyze", "monitor", "generate", "compare", "serve", "config-init"):
        assert cmd in result.output, f"Command '{cmd}' missing from --help output"


def test_analyze_help() -> None:
    """analyze --help shows the subcommand documentation."""
    result = runner.invoke(app, ["analyze", "--help"])
    assert result.exit_code == 0
    assert "URL" in result.output or "url" in result.output
    assert "--config" in result.output
    assert "--format" in result.output
    assert "--output" in result.output


def test_config_init(tmp_path) -> None:
    """config-init creates a valid YAML configuration template."""
    output_file = tmp_path / "geo-seo.yaml"
    result = runner.invoke(app, ["config-init", "--output", str(output_file)])
    assert result.exit_code == 0
    assert output_file.exists()

    content = output_file.read_text(encoding="utf-8")
    # Verify essential config sections are present
    assert "general:" in content
    assert "scoring:" in content
    assert "crawling:" in content
    assert "monitoring:" in content
    assert "database:" in content


def test_analyze_runs() -> None:
    """analyze command executes without error for a given URL."""
    result = runner.invoke(app, ["analyze", "https://example.com"])
    assert result.exit_code == 0
    assert "Analyse" in result.output or "analyze" in result.output.lower()


def test_monitor_runs() -> None:
    """monitor command executes without error for a given URL."""
    result = runner.invoke(app, ["monitor", "https://example.com"])
    assert result.exit_code == 0


def test_compare_runs() -> None:
    """compare command accepts multiple URLs."""
    result = runner.invoke(
        app, ["compare", "https://example.com", "https://example.org"]
    )
    assert result.exit_code == 0


def test_generate_runs() -> None:
    """generate command executes without error."""
    result = runner.invoke(app, ["generate", "https://example.com"])
    assert result.exit_code == 0


def test_serve_help() -> None:
    """serve --help shows host and port options."""
    result = runner.invoke(app, ["serve", "--help"])
    assert result.exit_code == 0
    assert "--host" in result.output
    assert "--port" in result.output
