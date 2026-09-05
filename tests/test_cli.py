import py_compile

from typer.testing import CliRunner

from scaffld import __version__
from scaffld.cli import app

runner = CliRunner()


def test_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_list_shows_templates():
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "python-lib" in result.output
    assert "python-cli" in result.output


def test_show_template_tree():
    result = runner.invoke(app, ["show", "python-lib"])
    assert result.exit_code == 0
    assert "pyproject.toml" in result.output


def test_show_unknown_template_fails():
    result = runner.invoke(app, ["show", "does-not-exist"])
    assert result.exit_code == 1


def test_new_no_input_generates(tmp_path):
    result = runner.invoke(
        app,
        [
            "new",
            "Demo Service",
            "--type",
            "python-cli",
            "--author",
            "Ada",
            "--no-venv",
            "--no-input",
            "--output",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0, result.output
    project = tmp_path / "demo-service"
    assert (project / "pyproject.toml").is_file()
    assert (project / "src" / "demo_service" / "cli.py").is_file()
    py_compile.compile(str(project / "src" / "demo_service" / "cli.py"), doraise=True)


def test_new_no_input_requires_type(tmp_path):
    result = runner.invoke(
        app, ["new", "Thing", "--no-input", "--output", str(tmp_path)]
    )
    assert result.exit_code == 1


def test_new_interactive_flow(tmp_path):
    # Feed: project name, template choice, author, email, description, license, confirm.
    answers = "\n".join(["Inter Active", "python-lib", "Ada", "", "A demo", "MIT", "y"])
    result = runner.invoke(
        app,
        ["new", "--no-venv", "--output", str(tmp_path)],
        input=answers + "\n",
    )
    assert result.exit_code == 0, result.output
    assert (tmp_path / "inter-active" / "pyproject.toml").is_file()


def test_list_survives_a_broken_user_template(tmp_path, monkeypatch):
    """A malformed manifest used to crash every command with a traceback."""
    broken = tmp_path / "broken"
    (broken / "files").mkdir(parents=True)
    (broken / "template.toml").write_text('[template\nname = "x"\n', encoding="utf-8")
    monkeypatch.setenv("SCAFFLD_TEMPLATES", str(tmp_path))

    result = runner.invoke(app, ["list"])

    assert result.exit_code == 0, result.output
    assert "python-lib" in result.output


def test_new_reports_render_errors_cleanly(tmp_path):
    """A bad filter in a user template is an `error:`, not a Rich traceback."""
    tpl = tmp_path / "tpl" / "bad"
    (tpl / "files").mkdir(parents=True)
    (tpl / "template.toml").write_text('[template]\nname = "bad"\n', encoding="utf-8")
    (tpl / "files" / "x.txt").write_text("{{ author | nope }}", encoding="utf-8")

    result = runner.invoke(
        app,
        ["new", "Z", "-t", "bad", "--no-input", "--no-venv", "-o", str(tmp_path / "o")],
        env={"SCAFFLD_TEMPLATES": str(tmp_path / "tpl")},
    )

    assert result.exit_code == 1
    assert "unknown filter" in result.output
    assert result.exception is None or isinstance(result.exception, SystemExit)


def test_new_rejects_bad_python_version(tmp_path):
    result = runner.invoke(
        app,
        [
            "new",
            "X",
            "-t",
            "python-lib",
            "--python",
            "banana",
            "--no-input",
            "--no-venv",
            "-o",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 1
    assert "--python must look like" in result.output


def test_new_accepts_patch_level_python_version(tmp_path):
    result = runner.invoke(
        app,
        [
            "new",
            "X",
            "-t",
            "python-lib",
            "--python",
            "3.9.1",
            "--no-input",
            "--no-venv",
            "-o",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0, result.output
    pyproject = (tmp_path / "x" / "pyproject.toml").read_text(encoding="utf-8")
    assert 'requires-python = ">=3.9.1"' in pyproject


def test_output_defaults_to_cwd_at_call_time(tmp_path, monkeypatch):
    """`-o` used to default to the directory scaffld was *imported* from."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(
        app, ["new", "P", "-t", "python-lib", "--no-input", "--no-venv"]
    )
    assert result.exit_code == 0, result.output
    assert (tmp_path / "p" / "pyproject.toml").is_file()


def test_new_reprompts_on_empty_project_name(tmp_path):
    """An empty name used to be accepted and create `<output>/package`."""
    answers = "\n".join(["", "  ", "Demo", "python-lib", "Ada", "", "", "MIT", "y"])
    result = runner.invoke(
        app, ["new", "--no-venv", "--output", str(tmp_path)], input=answers + "\n"
    )
    assert result.exit_code == 0, result.output
    assert (tmp_path / "demo" / "pyproject.toml").is_file()
    assert not (tmp_path / "package").exists()


def test_new_no_input_rejects_blank_name(tmp_path):
    result = runner.invoke(
        app, ["new", "   ", "-t", "python-lib", "--no-input", "-o", str(tmp_path)]
    )
    assert result.exit_code == 1
    assert "requires a project NAME" in result.output
