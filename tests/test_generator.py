import py_compile
import sys

import pytest

from scaffld import licenses, templates
from scaffld.context import ProjectContext
from scaffld.generator import GenerationError, create_virtualenv, generate


def _all_templates():
    return sorted(templates.discover())


def test_builtin_templates_present():
    names = _all_templates()
    assert {"python-lib", "python-cli", "python-api"} <= set(names)


@pytest.mark.parametrize("template_name", ["python-lib", "python-cli", "python-api"])
def test_generate_and_compile(tmp_path, template_name):
    template = templates.get(template_name)
    ctx = ProjectContext.build(
        "My Cool Thing",
        author="Ada Lovelace",
        author_email="ada@example.com",
        template=template_name,
    )
    result = generate(template, ctx, tmp_path / "out")
    root = result.target

    # Core files exist with placeholders resolved into real paths.
    assert (root / "pyproject.toml").is_file()
    assert (root / "README.md").is_file()
    assert (root / "LICENSE").is_file()
    assert (root / ".gitignore").is_file()
    assert (root / ".github" / "workflows" / "ci.yml").is_file()
    assert (root / "src" / "my_cool_thing" / "__init__.py").is_file()

    # No scaffld placeholders survive in text output...
    for rendered in result.created:
        text = (root / rendered).read_text(encoding="utf-8")
        for token in ("{{ project_name }}", "{{ package_name }}", "{{ author }}", "{% if"):
            assert token not in text, f"{token} left in {rendered}"

    # ...but GitHub Actions expressions are preserved untouched.
    ci = (root / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "${{ matrix.python-version }}" in ci

    # Every generated Python module compiles.
    for rendered in result.created:
        if rendered.suffix == ".py":
            py_compile.compile(str(root / rendered), doraise=True)


def test_license_none_skips_license_file(tmp_path):
    template = templates.get("python-lib")
    ctx = ProjectContext.build(
        "No License", author="Ada", license="none", template="python-lib"
    )
    result = generate(template, ctx, tmp_path / "out")
    assert not (result.target / "LICENSE").exists()
    assert all(r.name != "LICENSE" for r in result.created)


def test_refuses_nonempty_target(tmp_path):
    template = templates.get("python-lib")
    ctx = ProjectContext.build("X", author="Ada", template="python-lib")
    target = tmp_path / "out"
    target.mkdir()
    (target / "keep.txt").write_text("hi")
    with pytest.raises(GenerationError):
        generate(template, ctx, target)
    # force overrides
    result = generate(template, ctx, target, force=True)
    assert (result.target / "pyproject.toml").is_file()


def test_context_derives_names():
    ctx = ProjectContext.build("My Cool Thing", author="Ada", template="python-lib")
    assert ctx.package_name == "my_cool_thing"
    assert ctx.project_slug == "my-cool-thing"
    assert "MIT License" in ctx.license_text


def test_refuses_target_that_is_a_file(tmp_path):
    # Used to die with NotADirectoryError from iterdir(); must be a clean error.
    template = templates.get("python-lib")
    ctx = ProjectContext.build("X", author="Ada", template="python-lib")
    target = tmp_path / "out"
    target.write_text("i am a file")
    with pytest.raises(GenerationError, match="not a directory"):
        generate(template, ctx, target)


def test_rendered_path_cannot_escape_target(tmp_path):
    """A template variable used as a path segment must stay inside the target."""
    tpl = tmp_path / "tpl" / "esc"
    (tpl / "files").mkdir(parents=True)
    (tpl / "template.toml").write_text('[template]\nname = "esc"\n', encoding="utf-8")
    (tpl / "files" / "{{ author }}.txt").write_text("hi\n", encoding="utf-8")

    template = templates.Template(name="esc", description="", kind="generic", path=tpl)
    ctx = ProjectContext.build("Zed", author="../x", template="esc")
    target = tmp_path / "out" / "zed"
    with pytest.raises(GenerationError, match="escapes the target directory"):
        generate(template, ctx, target)
    assert not (tmp_path / "out" / "x.txt").exists()
    assert not (tmp_path / "x.txt").exists()


if sys.version_info >= (3, 11):  # pragma: no cover - version branch
    import tomllib
else:  # pragma: no cover - version branch
    import tomli as tomllib


@pytest.mark.parametrize("template_name", ["python-lib", "python-cli", "python-api"])
@pytest.mark.parametrize("license_id", ["MIT", "BSD-3-Clause", "ISC"])
def test_generated_pyproject_uses_spdx_license(tmp_path, template_name, license_id):
    """PEP 639 expression, not the deprecated `license = { text = ... }` table."""
    template = templates.get(template_name)
    ctx = ProjectContext.build(
        "Demo X", author="Ada", license=license_id, template=template_name
    )
    result = generate(template, ctx, tmp_path / "out")
    raw = (result.target / "pyproject.toml").read_text(encoding="utf-8")

    assert "{ text =" not in raw
    parsed = tomllib.loads(raw)
    assert parsed["project"]["license"] == license_id
    assert parsed["project"]["license-files"] == ["LICENSE"]
    assert (result.target / "LICENSE").is_file()


@pytest.mark.parametrize("template_name", ["python-lib", "python-cli", "python-api"])
def test_generated_pyproject_omits_license_when_none(tmp_path, template_name):
    """`-l none` used to declare `license = { text = "none" }` -- bogus metadata."""
    template = templates.get(template_name)
    ctx = ProjectContext.build(
        "Demo X", author="Ada", license="none", template=template_name
    )
    result = generate(template, ctx, tmp_path / "out")
    raw = (result.target / "pyproject.toml").read_text(encoding="utf-8")

    parsed = tomllib.loads(raw)
    assert "license" not in parsed["project"]
    assert "license-files" not in parsed["project"]
    assert not (result.target / "LICENSE").exists()


@pytest.mark.parametrize("license_id", licenses.CHOICES)
def test_every_license_choice_renders(license_id):
    text = licenses.render_license(license_id, "Ada Lovelace", 2026)
    if license_id == "none":
        assert text == ""
    else:
        assert "Ada Lovelace" in text
        assert "2026" in text


def test_create_virtualenv(tmp_path):
    # with_pip=False keeps this fast; the layout is what matters.
    venv_path = create_virtualenv(tmp_path, with_pip=False)
    assert venv_path == tmp_path / ".venv"
    assert (venv_path / "pyvenv.cfg").is_file()
