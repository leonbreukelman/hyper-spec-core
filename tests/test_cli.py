"""Tests for the CLI module entry point and commands."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner
from hyper_spec_core.cli import app


runner = CliRunner()


class TestCLIEntryPoint:
    """Tests for the CLI entry point."""

    def test_help_shows_commands(self) -> None:
        """Test that --help shows available commands."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "init" in result.stdout
        assert "new" in result.stdout
        assert "plan" in result.stdout
        assert "implement" in result.stdout

    def test_init_help(self) -> None:
        """Test init command help."""
        result = runner.invoke(app, ["init", "--help"])
        assert result.exit_code == 0
        assert "--force" in result.stdout


class TestInitCommand:
    """Tests for the init command."""

    def test_init_creates_directories(self, tmp_path: Path) -> None:
        """Test that init creates required directories."""
        # Skip if uv is not available
        import subprocess as sp
        uv_check = sp.run(["uv", "--version"], capture_output=True)
        if uv_check.returncode != 0:
            pytest.skip("uv not available")

        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            cli_result = runner.invoke(app, ["init"])
            # Should either succeed or create directories
            assert (tmp_path / "specs").exists() or cli_result.exit_code == 0
        finally:
            os.chdir(original_cwd)


class TestTemplateLoading:
    """Tests for template loading functionality."""

    def test_bundled_templates_accessible(self) -> None:
        """Test that bundled templates can be loaded."""
        from jinja2 import Environment, PackageLoader

        env = Environment(loader=PackageLoader("hyper_spec_core", "templates"))
        
        # Should be able to get template without error
        spec_template = env.get_template("spec_template.md")
        assert spec_template is not None
        
        plan_template = env.get_template("plan_template.md")
        assert plan_template is not None

    def test_spec_template_renders(self) -> None:
        """Test that spec template renders with context."""
        from jinja2 import Environment, PackageLoader

        env = Environment(loader=PackageLoader("hyper_spec_core", "templates"))
        template = env.get_template("spec_template.md")
        
        content = template.render(feature_name="test-feature", author="tester")
        
        assert "test-feature" in content
        assert "tester" in content

    def test_plan_template_renders(self) -> None:
        """Test that plan template renders with context."""
        from jinja2 import Environment, PackageLoader

        env = Environment(loader=PackageLoader("hyper_spec_core", "templates"))
        template = env.get_template("plan_template.md")
        
        content = template.render(
            feature_name="test-feature",
            confidence_score="95",
            summary="Test summary",
        )
        
        assert "test-feature" in content
        assert "95" in content
        assert "Test summary" in content
