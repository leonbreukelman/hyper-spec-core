"""Template resources for hyper-spec-core.

This package contains bundled Jinja2 templates for spec and plan generation.
Templates are loaded using importlib.resources when the package is installed,
or from local specs/.templates/ directory when available for customization.

Available templates:
- spec_template.md: Feature specification template
- plan_template.md: Implementation plan template
"""
