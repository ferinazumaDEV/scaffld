"""A tiny, dependency-free template engine.

Why not Jinja2? Scaffolding templates frequently contain GitHub Actions
expressions such as ``${{ matrix.python-version }}``. Jinja's default ``{{ }}``
delimiters collide with those, forcing awkward ``{% raw %}`` escaping in every
workflow file. ``scaffld`` sidesteps the whole problem with two rules:

* ``{{ name }}`` is substituted **only** when ``name`` is a known variable;
  anything else (``${{ github.sha }}``, ``{{ unknown }}``) is left byte-for-byte
  intact, so GitHub Actions files render correctly with no escaping.
* ``{% if x %} ... {% else %} ... {% endif %}`` blocks (nestable) allow a single
  template to serve several project shapes.

Supported variable filters: ``lower upper title capitalize snake kebab pascal
camel strip``. Chain them with ``|`` -> ``{{ project_name | snake }}``.
"""

from __future__ import annotations

import re
from typing import Callable, Mapping

from . import naming

FilterFn = Callable[[str], str]


class TemplateError(ValueError):
    """Raised when a template is malformed (bad tag, unclosed ``if``, ...)."""


_FILTERS: dict[str, FilterFn] = {
    "lower": str.lower,
    "upper": str.upper,
    "title": str.title,
    "capitalize": str.capitalize,
    "strip": str.strip,
    "snake": naming.snake_case,
    "kebab": naming.kebab_case,
    "pascal": naming.pascal_case,
    "camel": naming.camel_case,
}

# ``[^{}]`` keeps a match from ever spanning a ``}}`` boundary, which is what
# lets ``${{ github.sha }}`` be recognised as the inner ``{{ github.sha }}``.
_VAR_RE = re.compile(r"\{\{\s*([^{}]+?)\s*\}\}")
_TAG_RE = re.compile(r"\{%\s*(.+?)\s*%\}")
_EQ_RE = re.compile(r"""^([A-Za-z_]\w*)\s*(==|!=)\s*(.+)$""")


def _render_vars(text: str, ctx: Mapping[str, object]) -> str:
    def repl(match: "re.Match[str]") -> str:
        expr = match.group(1).strip()
        parts = [segment.strip() for segment in expr.split("|")]
        name = parts[0]
        if name not in ctx:
            # Unknown -> leave the original text untouched (GitHub Actions etc.).
            return match.group(0)
        value = str(ctx[name])
        for filter_name in parts[1:]:
            func = _FILTERS.get(filter_name)
            if func is None:
                raise TemplateError(f"unknown filter: {filter_name!r}")
            value = func(value)
        return value

    return _VAR_RE.sub(repl, text)


def _truthy(value: object) -> bool:
    if isinstance(value, str):
        return value.strip().lower() not in ("", "false", "0", "no", "none")
    return bool(value)


def evaluate_condition(expr: str, ctx: Mapping[str, object]) -> bool:
    """Evaluate an ``{% if %}`` expression.

    Supports ``name``, ``not name``, ``name == "value"`` and ``name != "value"``.
    """
    expr = expr.strip()
    negate = False
    if expr.startswith("not "):
        negate = True
        expr = expr[4:].strip()
    match = _EQ_RE.match(expr)
    if match:
        name, op, raw = match.group(1), match.group(2), match.group(3).strip()
        raw = raw.strip("\"'")
        actual = str(ctx.get(name, ""))
        result = actual == raw if op == "==" else actual != raw
    else:
        result = _truthy(ctx.get(expr))
    return not result if negate else result


def _tokenize(source: str) -> list[tuple[str, str]]:
    tokens: list[tuple[str, str]] = []
    last = 0
    for match in _TAG_RE.finditer(source):
        if match.start() > last:
            tokens.append(("text", source[last : match.start()]))
        tokens.append(("tag", match.group(1).strip()))
        last = match.end()
    if last < len(source):
        tokens.append(("text", source[last:]))
    return tokens


def _head(tag: str) -> str:
    return tag.split(None, 1)[0] if tag else ""


def _render_tokens(
    tokens: list[tuple[str, str]],
    pos: int,
    ctx: Mapping[str, object],
    stop: tuple[str, ...],
) -> tuple[str, int]:
    out: list[str] = []
    while pos < len(tokens):
        kind, value = tokens[pos]
        if kind == "text":
            out.append(_render_vars(value, ctx))
            pos += 1
            continue

        head = _head(value)
        if head in stop:
            return "".join(out), pos
        if head != "if":
            raise TemplateError(f"unexpected tag: {{% {value} %}}")

        condition = value[2:].strip()  # strip leading "if"
        true_branch, pos = _render_tokens(tokens, pos + 1, ctx, ("else", "endif"))
        if pos >= len(tokens):
            raise TemplateError("unclosed {% if %} block")
        false_branch = ""
        if _head(tokens[pos][1]) == "else":
            false_branch, pos = _render_tokens(tokens, pos + 1, ctx, ("endif",))
            if pos >= len(tokens):
                raise TemplateError("unclosed {% if %} block")
        pos += 1  # consume the endif
        out.append(true_branch if evaluate_condition(condition, ctx) else false_branch)
    return "".join(out), pos


def render_string(source: str, ctx: Mapping[str, object]) -> str:
    """Render ``source`` against ``ctx`` and return the result."""
    result, _ = _render_tokens(_tokenize(source), 0, ctx, ())
    return result
