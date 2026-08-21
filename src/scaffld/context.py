"""The variable set every template file is rendered against."""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass
from typing import Optional

from . import licenses, naming


@dataclass(frozen=True)
class ProjectContext:
    """Immutable bundle of the values used to render a project.

    Use :meth:`build` rather than constructing directly so that derived fields
    (``package_name``, ``project_slug``, ``license_text`` ...) stay consistent.
    """

    project_name: str
    package_name: str
    project_slug: str
    author: str
    author_email: str
    description: str
    license: str
    license_text: str
    python_version: str
    year: int
    template: str

    @classmethod
    def build(
        cls,
        project_name: str,
        *,
        author: str,
        template: str,
        author_email: str = "",
        description: str = "",
        license: str = licenses.DEFAULT,
        python_version: str = "3.9",
        year: Optional[int] = None,
    ) -> "ProjectContext":
        if license not in licenses.CHOICES:
            raise ValueError(
                f"unknown license {license!r}; choose from {', '.join(licenses.CHOICES)}"
            )
        resolved_year = year if year is not None else _dt.date.today().year
        pkg = naming.package_name(project_name)
        return cls(
            project_name=project_name,
            package_name=pkg,
            project_slug=naming.kebab_case(project_name) or pkg,
            author=author,
            author_email=author_email,
            description=description or f"{project_name}, a Python project.",
            license=license,
            license_text=licenses.render_license(license, author, resolved_year),
            python_version=python_version,
            year=resolved_year,
            template=template,
        )

    def as_dict(self) -> dict[str, object]:
        """Return the flat mapping the renderer consumes."""
        return {
            "project_name": self.project_name,
            "package_name": self.package_name,
            "project_slug": self.project_slug,
            "author": self.author,
            "author_email": self.author_email,
            "description": self.description,
            "license": self.license,
            "license_text": self.license_text,
            "python_version": self.python_version,
            "year": self.year,
            "template": self.template,
            # Convenience booleans for {% if %} blocks in templates.
            "has_license": self.license != "none",
            "has_email": bool(self.author_email),
        }
