import pytest

from scaffld import templates
from scaffld.context import ProjectContext
from scaffld.generator import generate


def _make_user_template(root, name="my-custom"):
    tpl = root / name
    files = tpl / "files"
    files.mkdir(parents=True)
    (tpl / "template.toml").write_text(
        f'[template]\nname = "{name}"\nkind = "custom"\n'
        'description = "A user template."\n',
        encoding="utf-8",
    )
    (files / "hello.txt").write_text("Hi {{ author }} from {{ project_name }}!\n")
    (files / "{{ package_name }}.py").write_text("VALUE = '{{ project_slug }}'\n")
    return tpl


def test_discover_picks_up_user_templates(tmp_path, monkeypatch):
    _make_user_template(tmp_path)
    monkeypatch.setenv("SCAFFLD_TEMPLATES", str(tmp_path))
    found = templates.discover()
    assert "my-custom" in found
    assert found["my-custom"].kind == "custom"


def test_user_template_shadows_builtin(tmp_path, monkeypatch):
    # A user template named like a built-in one takes precedence.
    _make_user_template(tmp_path, name="python-lib")
    monkeypatch.setenv("SCAFFLD_TEMPLATES", str(tmp_path))
    found = templates.discover()
    assert found["python-lib"].kind == "custom"


def test_generate_from_user_template(tmp_path, monkeypatch):
    src = tmp_path / "src_templates"
    src.mkdir()
    _make_user_template(src)
    monkeypatch.setenv("SCAFFLD_TEMPLATES", str(src))

    template = templates.get("my-custom")
    ctx = ProjectContext.build("Cool Thing", author="Ada", template="my-custom")
    result = generate(template, ctx, tmp_path / "out")

    assert (result.target / "hello.txt").read_text().strip() == "Hi Ada from Cool Thing!"
    # Path segment placeholder was rendered into a real filename.
    assert (result.target / "cool_thing.py").read_text().strip() == "VALUE = 'cool-thing'"


def test_get_unknown_template_raises():
    with pytest.raises(templates.TemplateError):
        templates.get("nope-not-real")
