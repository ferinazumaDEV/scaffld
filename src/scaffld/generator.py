"""Turn a :class:`~scaffld.templates.Template` + context into files on disk."""

from __future__ import annotations

import os
import venv
from dataclasses import dataclass
from pathlib import Path

from .context import ProjectContext
from .render import render_string
from .templates import Template


class GenerationError(Exception):
    """Raised when generation cannot proceed (target not empty, collision...)."""


@dataclass
class GenerationResult:
    """What :func:`generate` produced."""

    target: Path
    created: list[Path]  # paths relative to ``target``
    venv_path: Path | None = None


def _render_relpath(relative: Path, ctx: dict[str, object]) -> Path | None:
    """Render each path segment; return ``None`` if any renders empty (skip).

    Template variables are user input, so a segment such as ``{{ author }}`` can
    render to ``../../escaped``. Reject any segment that is ``..`` or that
    carries a path separator, naming the offending one.
    """
    parts = [render_string(part, ctx) for part in relative.parts]
    if any(part == "" for part in parts):
        return None
    separators = [sep for sep in (os.sep, os.altsep) if sep]
    for part in parts:
        if part == ".." or any(sep in part for sep in separators):
            raise GenerationError(
                f"template path escapes the target directory: {part!r} "
                f"(rendered from {relative.as_posix()!r})"
            )
    return Path(*parts)


def generate(
    template: Template,
    context: ProjectContext,
    target_dir: Path,
    *,
    force: bool = False,
) -> GenerationResult:
    """Render ``template`` into ``target_dir`` using ``context``.

    ``target_dir`` may already exist but must be empty unless ``force`` is set.
    Path segments and file contents are both rendered; a file whose ``LICENSE``
    name pairs with ``license == "none"`` is skipped.
    """
    target_dir = target_dir.resolve()
    if target_dir.exists() and not target_dir.is_dir():
        raise GenerationError(f"target path exists and is not a directory: {target_dir}")
    if target_dir.exists() and any(target_dir.iterdir()) and not force:
        raise GenerationError(f"target directory is not empty: {target_dir}")

    ctx = context.as_dict()
    created: list[Path] = []

    for source in template.iter_files():
        relative = source.relative_to(template.files_root)
        rendered_rel = _render_relpath(relative, ctx)
        if rendered_rel is None:
            continue
        if rendered_rel.name == "LICENSE" and context.license == "none":
            continue

        try:
            text = source.read_text(encoding="utf-8")
            data = render_string(text, ctx).encode("utf-8")
        except UnicodeDecodeError:
            data = source.read_bytes()  # binary asset: copy verbatim

        destination = target_dir / rendered_rel
        if not destination.resolve().is_relative_to(target_dir):
            raise GenerationError(
                "template path escapes the target directory: "
                f"{rendered_rel.as_posix()!r}"
            )
        if destination.exists() and not force:
            raise GenerationError(f"refusing to overwrite: {destination}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        created.append(rendered_rel)

    return GenerationResult(target=target_dir, created=sorted(created))


def create_virtualenv(target_dir: Path, *, with_pip: bool = True) -> Path:
    """Create a ``.venv`` inside ``target_dir`` and return its path.

    ``with_pip=False`` skips bootstrapping pip -- handy for fast tests.
    """
    venv_path = target_dir / ".venv"
    builder = venv.EnvBuilder(with_pip=with_pip, clear=False, symlinks=True)
    builder.create(str(venv_path))
    return venv_path
