import py_compile

import pytest

from scaffld import templates
from scaffld.context import ProjectContext
from scaffld.generator import GenerationError, generate


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
