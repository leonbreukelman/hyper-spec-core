"""Tests for the Governance Adapter module."""

from __future__ import annotations

import pytest
from pathlib import Path
from hyper_spec_core.adapter import GovernanceAdapter, GovernanceContext


class TestGovernanceContext:
    """Tests for the GovernanceContext dataclass."""

    def test_to_system_prompt_with_all_fields(self) -> None:
        """Test prompt generation with all fields populated."""
        ctx = GovernanceContext(
            allowed_libs=["fastapi", "pydantic"],
            banned_libs=["pickle", "eval"],
            security_controls="No SQL injection",
            architectural_layers="Domain -> Application -> Infrastructure",
        )

        prompt = ctx.to_system_prompt()

        assert "fastapi, pydantic" in prompt
        assert "pickle, eval" in prompt
        assert "No SQL injection" in prompt
        assert "Domain -> Application -> Infrastructure" in prompt
        assert "[TECHNOLOGY STACK]" in prompt
        assert "[SECURITY CONTROLS]" in prompt
        assert "[ARCHITECTURAL LAYERS]" in prompt

    def test_to_system_prompt_with_empty_lists(self) -> None:
        """Test prompt generation with empty library lists."""
        ctx = GovernanceContext()

        prompt = ctx.to_system_prompt()

        assert "None specified" in prompt

    def test_to_system_prompt_without_optional_sections(self) -> None:
        """Test prompt generation without security/architecture sections."""
        ctx = GovernanceContext(
            allowed_libs=["requests"],
            banned_libs=[],
        )

        prompt = ctx.to_system_prompt()

        assert "requests" in prompt
        # Optional sections should not appear if empty
        assert "[SECURITY CONTROLS]" not in prompt
        assert "[ARCHITECTURAL LAYERS]" not in prompt


class TestGovernanceAdapter:
    """Tests for the GovernanceAdapter class."""

    @pytest.fixture
    def valid_codex_dir(self, tmp_path: Path) -> Path:
        """Create a valid .codex directory with all artifacts."""
        codex = tmp_path / ".codex"
        codex.mkdir()

        # Create stack.yaml
        (codex / "stack.yaml").write_text("""
rules:
  material:
    stack:
      allowed_libraries:
        - fastapi
        - pydantic
        - sqlmodel
      banned_libraries:
        - pickle
        - eval
""")

        # Create security.md
        (codex / "security.md").write_text("""
# Security Controls

<!-- BEGIN_CONTROLS -->
- Never use eval() or exec()
- Always sanitize user input
- Use parameterized queries
<!-- END_CONTROLS -->

Other content here.
""")

        # Create architecture.md
        (codex / "architecture.md").write_text("""
# Architecture

<!-- BEGIN_LAYERS -->
Domain Layer: Pure business logic
Application Layer: Use cases and orchestration
Infrastructure Layer: External dependencies
<!-- END_LAYERS -->
""")

        return codex

    @pytest.fixture
    def minimal_codex_dir(self, tmp_path: Path) -> Path:
        """Create a .codex directory with only required stack.yaml (nested format)."""
        codex = tmp_path / ".codex"
        codex.mkdir()

        # Create minimal stack.yaml in nested format
        (codex / "stack.yaml").write_text("""
rules:
  material:
    stack:
      allowed_libraries: []
      banned_libraries: []
""")

        return codex

    @pytest.fixture
    def flat_format_codex_dir(self, tmp_path: Path) -> Path:
        """Create a .codex directory with flat stack.yaml format (actual codex weave output)."""
        codex = tmp_path / ".codex"
        codex.mkdir()

        # Create stack.yaml in flat format (actual codex weave output)
        (codex / "stack.yaml").write_text("""
python_version: '3.11'
allowed_libraries:
  - pyyaml
  - click
  - rich
banned_libraries:
  - pickle
  - os.system
required_tools:
  - ruff
  - mypy
""")

        # Create security.md with anchors
        (codex / "security.md").write_text("""
# Security

<!-- BEGIN_CONTROLS -->
No arbitrary code execution allowed.
<!-- END_CONTROLS -->
""")

        # Create architecture.md with anchors
        (codex / "architecture.md").write_text("""
# Architecture

<!-- BEGIN_LAYERS -->
Domain | Application | Infrastructure
<!-- END_LAYERS -->
""")

        return codex

    def test_load_context_valid(self, valid_codex_dir: Path) -> None:
        """Test loading context from valid artifacts (nested format)."""
        adapter = GovernanceAdapter(valid_codex_dir)
        ctx = adapter.load_context()

        assert ctx.allowed_libs == ["fastapi", "pydantic", "sqlmodel"]
        assert ctx.banned_libs == ["pickle", "eval"]
        assert "Never use eval()" in ctx.security_controls
        assert "Domain Layer" in ctx.architectural_layers

    def test_load_context_flat_format(self, flat_format_codex_dir: Path) -> None:
        """Test loading context from flat format artifacts (actual codex weave output)."""
        adapter = GovernanceAdapter(flat_format_codex_dir)
        ctx = adapter.load_context()

        assert ctx.allowed_libs == ["pyyaml", "click", "rich"]
        assert ctx.banned_libs == ["pickle", "os.system"]
        assert "No arbitrary code execution" in ctx.security_controls
        assert "Domain | Application | Infrastructure" in ctx.architectural_layers

    def test_load_context_missing_directory(self, tmp_path: Path) -> None:
        """Test that missing directory raises FileNotFoundError."""
        adapter = GovernanceAdapter(tmp_path / "nonexistent")

        with pytest.raises(FileNotFoundError) as exc_info:
            adapter.load_context()

        assert "Governance artifacts not found" in str(exc_info.value)
        assert "codex weave" in str(exc_info.value)

    def test_load_context_missing_stack_yaml(self, tmp_path: Path) -> None:
        """Test that missing stack.yaml raises FileNotFoundError."""
        codex = tmp_path / ".codex"
        codex.mkdir()
        # Don't create stack.yaml

        adapter = GovernanceAdapter(codex)

        with pytest.raises(FileNotFoundError) as exc_info:
            adapter.load_context()

        assert "stack.yaml" in str(exc_info.value)

    def test_load_context_missing_optional_files(
        self, minimal_codex_dir: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test graceful degradation when optional files are missing."""
        adapter = GovernanceAdapter(minimal_codex_dir)
        ctx = adapter.load_context()

        # Should still return context with empty optional fields
        assert ctx.security_controls == ""
        assert ctx.architectural_layers == ""

        # Should have printed warnings
        captured = capsys.readouterr()
        assert "security.md" in captured.err
        assert "architecture.md" in captured.err

    def test_parse_stack_yaml_missing_keys(self, tmp_path: Path) -> None:
        """Test defensive parsing when YAML keys are missing."""
        codex = tmp_path / ".codex"
        codex.mkdir()

        # Create stack.yaml with partial structure
        (codex / "stack.yaml").write_text("""
rules:
  material:
    other_key: value
""")

        adapter = GovernanceAdapter(codex)
        ctx = adapter.load_context()

        # Should default to empty lists
        assert ctx.allowed_libs == []
        assert ctx.banned_libs == []

    def test_extract_section_valid(self) -> None:
        """Test regex extraction with valid anchor tags."""
        content = """
Some preamble

<!-- BEGIN_TEST -->
This is the content
with multiple lines
<!-- END_TEST -->

Some epilogue
"""
        result = GovernanceAdapter._extract_section(
            content, "<!-- BEGIN_TEST -->", "<!-- END_TEST -->"
        )

        assert result == "This is the content\nwith multiple lines"

    def test_extract_section_missing_tags(self) -> None:
        """Test regex extraction when tags are missing."""
        content = "No tags here at all"

        result = GovernanceAdapter._extract_section(
            content, "<!-- BEGIN_TEST -->", "<!-- END_TEST -->"
        )

        assert result == ""

    def test_extract_section_malformed_tags(self) -> None:
        """Test regex extraction with incomplete tags."""
        content = """
<!-- BEGIN_TEST -->
Content here but no closing tag
"""
        result = GovernanceAdapter._extract_section(
            content, "<!-- BEGIN_TEST -->", "<!-- END_TEST -->"
        )

        assert result == ""

    def test_extract_section_with_warning(
        self, valid_codex_dir: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test that missing sections in existing files produce warnings."""
        # Overwrite security.md without anchor tags
        (valid_codex_dir / "security.md").write_text("No anchors here")

        adapter = GovernanceAdapter(valid_codex_dir)
        ctx = adapter.load_context()

        assert ctx.security_controls == ""

        captured = capsys.readouterr()
        assert "Security Controls" in captured.err
