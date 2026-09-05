"""Case-conversion helpers used by templates and the rendering context.

Every function is total: given any string it returns a best-effort conversion,
splitting on non-alphanumeric characters *and* on ``camelCase`` boundaries so
that ``"My Cool-Lib"``, ``"myCoolLib"`` and ``"my_cool_lib"`` all normalise to
the same word list.
"""

from __future__ import annotations

import keyword
import re
import unicodedata

# Letters that NFKD does not decompose into "ASCII letter + combining mark".
_TRANSLITERATE = str.maketrans(
    {
        "\u00df": "ss",  # LATIN SMALL LETTER SHARP S
        "\u1e9e": "SS",  # LATIN CAPITAL LETTER SHARP S
        "\u00f8": "o",
        "\u00d8": "O",
        "\u00e6": "ae",
        "\u00c6": "AE",
        "\u0153": "oe",
        "\u0152": "OE",
        "\u0111": "d",
        "\u0110": "D",
        "\u00f0": "d",
        "\u00d0": "D",
        "\u0142": "l",
        "\u0141": "L",
        "\u00fe": "th",
        "\u00de": "TH",
    }
)

_WORD_RE = re.compile(r"[A-Za-z0-9]+")
_LOWER_UPPER = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
_UPPER_RUN = re.compile(r"(?<=[A-Z])(?=[A-Z][a-z])")


def asciify(value: str) -> str:
    """Transliterate ``value`` to ASCII.

    Without this every non-ASCII letter counts as a word separator and names
    are shredded mid-word: ``"Caf\u00e9 B\u00faho"`` -> ``caf_b_ho``. Accents are
    dropped via NFKD; the few letters that do not decompose are mapped by hand
    (``\u00df`` -> ``ss``, ``\u00f8`` -> ``o``, ``\u00e6`` -> ``ae``, ``\u0111`` -> ``d``, ``\u0142`` -> ``l``).
    """
    decomposed = unicodedata.normalize("NFKD", value.translate(_TRANSLITERATE))
    return decomposed.encode("ascii", "ignore").decode("ascii")


def words(value: str) -> list[str]:
    """Split ``value`` into its constituent words.

    Handles spaces, dashes, underscores and ``camelCase``/``PascalCase``
    boundaries, e.g. ``"HTTPServer2"`` -> ``["HTTP", "Server2"]``. Non-ASCII
    letters are transliterated first (see :func:`asciify`), so
    ``"Caf\u00e9 B\u00faho"`` -> ``["Cafe", "Buho"]``.
    """
    spaced = _LOWER_UPPER.sub(" ", asciify(value))
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

    Falls back to ``"package"`` for input that has no usable characters,
    prefixes a leading underscore when the result would start with a digit, and
    appends one when the result is a Python keyword (``class`` -> ``class_``),
    which would otherwise generate a project that cannot even be imported.
    """
    name = snake_case(value)
    if not name:
        return "package"
    if name[0].isdigit():
        name = f"_{name}"
    if keyword.iskeyword(name):
        name = f"{name}_"
    return name
