"""The generated project must parse, whatever the user typed.

Audit finding F03. `scaffld` interpolated author and description into
`pyproject.toml` and into Python source as plain text, so any value containing a
character that is special in the destination grammar produced a project that
would not parse. An author called `Ana "AI"` was enough:

    authors = [{ name = "Ana "AI"" }]      ->  TOMLDecodeError

Nine of twelve template/input combinations failed. The existing end-to-end test
passed throughout, because it generates with one benign name.

The fix is per-format escaping — `| toml` and `| py` filters — so these tests
assert the property that matters: for every template and every input the CLI
accepts, the generated TOML loads and the generated Python parses.
"""

from __future__ import annotations

import ast
import tempfile
import tomllib
from pathlib import Path

import pytest

from scaffld.context import ProjectContext
from scaffld.generator import generate
from scaffld.render import python_string, toml_string
from scaffld.templates import get

TEMPLATES = ["python-lib", "python-cli", "python-api"]

HOSTILE = [
    pytest.param('Ana "AI"', 'A "quoted" description', id="double-quotes"),
    pytest.param("C:\\Users\\ana", "a path C:\\tmp\\x", id="backslashes"),
    pytest.param("Ana", "first line\nsecond line", id="newline"),
    pytest.param("Café Búho ñ 😀", "Acentuación y emoji 😀", id="unicode"),
    pytest.param('Ana"', 'ends with a quote"', id="trailing-quote"),
    pytest.param("Ana\tLovelace", "tab\tseparated", id="tab"),
    pytest.param("Ada Lovelace", "A tiny weather CLI.", id="control-benign"),
]


@pytest.mark.parametrize("template", TEMPLATES)
@pytest.mark.parametrize("author,description", HOSTILE)
def test_generated_project_parses(template, author, description):
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "demo"
        context = ProjectContext.build(
            "audit-demo", author=author, description=description, template=template
        )
        generate(get(template), context, target)

        # The metadata a build backend will read.
        data = tomllib.loads((target / "pyproject.toml").read_text(encoding="utf-8"))
        assert data["project"]["description"] == description
        assert data["project"]["authors"][0]["name"] == author

        # Every Python file it wrote.
        for source in target.rglob("*.py"):
            ast.parse(source.read_text(encoding="utf-8"), filename=str(source))


@pytest.mark.parametrize("raw", [
    'Ana "AI"', "back\\slash", "line\nbreak", "tab\there", "bell\x07", "ok",
])
def test_toml_filter_round_trips(raw):
    """Escaping is only correct if the value survives it."""
    document = f'value = "{toml_string(raw)}"'
    assert tomllib.loads(document)["value"] == raw


@pytest.mark.parametrize("raw", [
    'Ana "AI"', "back\\slash", "line\nbreak", "tab\there", 'ends"', "ok",
])
def test_py_filter_round_trips(raw):
    """Safe inside both a plain and a triple-quoted literal."""
    for literal in (f'"{python_string(raw)}"', f'"""{python_string(raw)}"""'):
        assert ast.literal_eval(literal) == raw
