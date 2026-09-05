"""Discovery and loading of scaffold templates.

A *template* is a directory containing:

* ``template.toml`` -- a manifest with a ``[template]`` table
  (``name``, ``description``, optional ``kind``);
* ``files/`` -- the tree that gets rendered into the new project. Both file
  contents *and* path segments may contain ``{{ variables }}``.

Templates are discovered from, in increasing precedence:

1. the built-in directory bundled with this package;
2. ``~/.scaffld/templates`` (override via ``SCAFFLD_TEMPLATES``, an
   ``os.pathsep``-separated list of extra directories).

A user template whose name matches a built-in one shadows it.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional

if sys.version_info >= (3, 11):  # pragma: no cover - version branch
    import tomllib
else:  # pragma: no cover - version branch
    import tomli as tomllib

BUILTIN_DIR = Path(__file__).resolve().parent / "builtins"
USER_DIR = Path.home() / ".scaffld" / "templates"


class TemplateError(Exception):
    """Raised for a missing or malformed template."""


@dataclass(frozen=True)
class Template:
    """A loaded template: its metadata plus the location of its ``files/`` tree."""

    name: str
    description: str
    kind: str
    path: Path

    @property
    def files_root(self) -> Path:
        return self.path / "files"

    def iter_files(self) -> Iterator[Path]:
        """Yield every regular file under ``files/`` (skipping caches)."""
        root = self.files_root
        for entry in sorted(root.rglob("*")):
            if entry.is_dir():
                continue
            if "__pycache__" in entry.parts or entry.name.endswith(".pyc"):
                continue
            yield entry


def _load_template(path: Path) -> Optional[Template]:
    manifest = path / "template.toml"
    if not manifest.is_file() or not (path / "files").is_dir():
        return None
    try:
        data = tomllib.loads(manifest.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        # One malformed user template must not take down `scaffld list` (and
        # every other command): warn on stderr and carry on without it.
        print(f"warning: skipping {manifest}: {exc}", file=sys.stderr)
        return None
    meta = data.get("template", {})
    name = str(meta.get("name") or path.name)
    return Template(
        name=name,
        description=str(meta.get("description", "")),
        kind=str(meta.get("kind", "generic")),
        path=path,
    )


def _search_dirs(extra: Optional[list[Path]] = None) -> list[Path]:
    dirs: list[Path] = [BUILTIN_DIR, USER_DIR]
    env = os.environ.get("SCAFFLD_TEMPLATES")
    if env:
        dirs.extend(Path(p) for p in env.split(os.pathsep) if p)
    if extra:
        dirs.extend(extra)
    return dirs


def discover(extra_dirs: Optional[list[Path]] = None) -> dict[str, Template]:
    """Return ``{name: Template}`` for all templates, later dirs winning ties."""
    found: dict[str, Template] = {}
    for directory in _search_dirs(extra_dirs):
        if not directory.is_dir():
            continue
        for child in sorted(directory.iterdir()):
            if not child.is_dir():
                continue
            template = _load_template(child)
            if template is not None:
                found[template.name] = template
    return found


def get(name: str, extra_dirs: Optional[list[Path]] = None) -> Template:
    """Return the template called ``name`` or raise :class:`TemplateError`."""
    templates = discover(extra_dirs)
    try:
        return templates[name]
    except KeyError:
        available = ", ".join(sorted(templates)) or "(none)"
        raise TemplateError(
            f"unknown template {name!r}; available: {available}"
        ) from None
