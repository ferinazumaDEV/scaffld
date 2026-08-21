"""Case-conversion helpers used by templates and the rendering context.

Every function is total: given any string it returns a best-effort conversion,
splitting on non-alphanumeric characters *and* on ``camelCase`` boundaries so
that ``"My Cool-Lib"``, ``"myCoolLib"`` and ``"my_cool_lib"`` all normalise to
the same word list.
"""

from __future__ import annotations

import re

_WORD_RE = re.compile(r"[A-Za-z0-9]+")
_LOWER_UPPER = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
_UPPER_RUN = re.compile(r"(?<=[A-Z])(?=[A-Z][a-z])")


def words(value: str) -> list[str]:
    """Split ``value`` into its constituent words.

    Handles spaces, dashes, underscores and ``camelCase``/``PascalCase``
    boundaries, e.g. ``"HTTPServer2"`` -> ``["HTTP", "Server2"]``.
    """
    spaced = _LOWER_UPPER.sub(" ", value)
    spaced = _UPPER_RUN.sub(" ", spaced)
    return _WORD_RE.findall(spaced)


def snake_case(value: str) -> str:
    """``"My Cool-Lib"`` -> ``"my_cool_lib"``."""
    return "_".join(word.lower() for word in words(value))


def kebab_case(value: str) -> str:
    """``"My Cool Lib"`` -> ``"my-cool-lib"``."""
    return "-".join(word.lower() for word in words(value))


def pascal_case(value: str) -> str:
    """``"my cool lib"`` -> ``"MyCoolLib"``."""
    return "".join(word.capitalize() for word in words(value))


def camel_case(value: str) -> str:
    """``"my cool lib"`` -> ``"myCoolLib"``."""
    parts = words(value)
    if not parts:
        return ""
    return parts[0].lower() + "".join(word.capitalize() for word in parts[1:])


def package_name(value: str) -> str:
    """Return a valid, importable Python package name derived from ``value``.

    Falls back to ``"package"`` for input that has no usable characters, and
    prefixes a leading underscore when the result would start with a digit.
    """
    name = snake_case(value)
    if not name:
        return "package"
    if name[0].isdigit():
        name = f"_{name}"
    return name
