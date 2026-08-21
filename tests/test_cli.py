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
