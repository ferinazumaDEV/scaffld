"""``scaffld`` command-line interface (Typer + Rich)."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.tree import Tree

from . import __version__, licenses
from .context import ProjectContext
from .generator import GenerationError, create_virtualenv, generate
from .render import RenderError
from .templates import Template, TemplateError, discover, get

#: `requires-python = ">={{ python_version }}"` has to stay a valid PEP 508
#: specifier, so only "3.N" and "3.N.P" are accepted.
_PYTHON_VERSION_RE = re.compile(r"3\.\d{1,2}(\.\d+)?")

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Scaffold new projects in seconds with a friendly TUI.",
)
console = Console()


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _git_config(key: str) -> Optional[str]:
    try:
        out = subprocess.run(
            ["git", "config", "--get", key],
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    value = out.stdout.strip()
    return value or None


def _default_author() -> str:
    return (
        os.environ.get("SCAFFLD_AUTHOR")
        or _git_config("user.name")
        or os.environ.get("USER")
        or "Your Name"
    )


def _default_email() -> str:
    return os.environ.get("SCAFFLD_EMAIL") or _git_config("user.email") or ""


def _templates_table(templates: dict[str, Template]) -> Table:
    table = Table(title="Available templates", title_style="bold cyan", expand=False)
    table.add_column("#", style="dim", justify="right")
    table.add_column("Template", style="bold green")
    table.add_column("Kind", style="magenta")
    table.add_column("Description")
    for index, name in enumerate(sorted(templates), start=1):
        tpl = templates[name]
        table.add_row(str(index), tpl.name, tpl.kind, tpl.description)
    return table


def _choose_template(templates: dict[str, Template]) -> str:
    names = sorted(templates)
    console.print(_templates_table(templates))
    while True:
        raw = Prompt.ask("Select a template (number or name)", default=names[0])
        if raw in templates:
            return raw
        if raw.isdigit() and 1 <= int(raw) <= len(names):
            return names[int(raw) - 1]
        console.print(f"[red]'{raw}' is not a valid choice.[/red]")


def _files_tree(target: Path, created: list[Path]) -> Tree:
    tree = Tree(f"[bold]{target.name}/[/bold]", guide_style="dim")
    nodes: dict[Path, Tree] = {Path("."): tree}
    for rel in created:
        parent = tree
        accumulated = Path(".")
        for part in rel.parts[:-1]:
            accumulated = accumulated / part
            if accumulated not in nodes:
                nodes[accumulated] = parent.add(f"[cyan]{part}/[/cyan]")
            parent = nodes[accumulated]
        parent.add(rel.parts[-1])
    return tree


def _abort(message: str) -> "typer.Exit":
    console.print(f"[bold red]error:[/bold red] {message}")
    return typer.Exit(code=1)


# --------------------------------------------------------------------------- #
# commands
# --------------------------------------------------------------------------- #
@app.command("list")
def list_templates() -> None:
    """List every available template (built-in and user-defined)."""
    templates = discover()
    if not templates:
        console.print("[yellow]No templates found.[/yellow]")
        raise typer.Exit(code=0)
    console.print(_templates_table(templates))


@app.command()
def show(name: str = typer.Argument(..., help="Template name.")) -> None:
    """Show the file tree a template would generate."""
    try:
        template = get(name)
    except TemplateError as exc:
        raise _abort(str(exc))
    tree = Tree(f"[bold green]{template.name}[/bold green]  [dim]{template.kind}[/dim]")
    for source in template.iter_files():
        rel = source.relative_to(template.files_root)
        tree.add(str(rel))
    console.print(Panel(template.description or "(no description)", title="Description"))
    console.print(tree)


@app.command()
def new(
    name: Optional[str] = typer.Argument(None, help="Project name."),
    template: Optional[str] = typer.Option(
        None, "--type", "-t", help="Template to use (see `scaffld list`)."
    ),
    author: Optional[str] = typer.Option(None, "--author", "-a"),
    email: Optional[str] = typer.Option(None, "--email"),
    description: Optional[str] = typer.Option(None, "--description", "-d"),
    license: Optional[str] = typer.Option(
        None, "--license", "-l", help=f"One of: {', '.join(licenses.CHOICES)}."
    ),
    python_version: str = typer.Option("3.9", "--python", help="Minimum Python."),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Directory to create the project in (default: current directory).",
    ),
    venv: bool = typer.Option(True, "--venv/--no-venv", help="Create a .venv."),
    force: bool = typer.Option(False, "--force", help="Write into a non-empty dir."),
    no_input: bool = typer.Option(
        False, "--no-input", help="Never prompt; fail if a required value is missing."
    ),
) -> None:
    """Create a new project from a template."""
    # Evaluated here, not in the default above: `Path.cwd()` in a Typer default
    # is frozen at import time and would ignore any later chdir.
    output = output or Path.cwd()
    if not _PYTHON_VERSION_RE.fullmatch(python_version):
        raise _abort(f"--python must look like 3.N (e.g. 3.11), got {python_version!r}")

    templates = discover()
    if not templates:
        raise _abort("no templates available")

    if no_input:
        if not (name and name.strip()):
            raise _abort("--no-input requires a project NAME")
        if not template:
            raise _abort("--no-input requires --type")
        resolved_author = author or _default_author()
        resolved_email = email or _default_email()
        resolved_license = license or licenses.DEFAULT
        resolved_desc = description or ""
    else:
        console.print(
            Panel.fit(
                "[bold cyan]scaffld[/bold cyan] — new project",
                border_style="cyan",
            )
        )
        while not (name and name.strip()):
            name = Prompt.ask("Project name")
        template = template or _choose_template(templates)
        resolved_author = author or Prompt.ask("Author", default=_default_author())
        resolved_email = email or Prompt.ask(
            "Author email", default=_default_email(), show_default=bool(_default_email())
        )
        resolved_desc = description if description is not None else Prompt.ask(
            "Description", default=""
        )
        resolved_license = license or Prompt.ask(
            "License", choices=list(licenses.CHOICES), default=licenses.DEFAULT
        )

    name = name.strip()
    if template not in templates:
        raise _abort(
            f"unknown template {template!r}; available: {', '.join(sorted(templates))}"
        )
    if resolved_license not in licenses.CHOICES:
        raise _abort(
            f"unknown license {resolved_license!r}; choose from "
            f"{', '.join(licenses.CHOICES)}"
        )

    context = ProjectContext.build(
        name,
        author=resolved_author,
        author_email=resolved_email,
        description=resolved_desc,
        license=resolved_license,
        python_version=python_version,
        template=template,
    )
    target = (output / context.project_slug).resolve()

    if not no_input:
        summary = Table.grid(padding=(0, 2))
        summary.add_column(style="bold")
        summary.add_column()
        summary.add_row("Template", template)
        summary.add_row("Package", context.package_name)
        summary.add_row("Author", context.author)
        summary.add_row("License", context.license)
        summary.add_row("Location", str(target))
        summary.add_row("Virtualenv", "yes" if venv else "no")
        console.print(Panel(summary, title="About to create", border_style="green"))
        if not Confirm.ask("Proceed?", default=True):
            console.print("[yellow]Aborted.[/yellow]")
            raise typer.Exit(code=0)

    try:
        result = generate(templates[template], context, target, force=force)
    except (GenerationError, RenderError) as exc:
        raise _abort(str(exc))

    if venv:
        if console.is_terminal:
            with console.status("[cyan]Creating virtual environment...[/cyan]"):
                result.venv_path = create_virtualenv(target)
        else:
            result.venv_path = create_virtualenv(target)

    console.print(_files_tree(target, result.created))
    done = Table.grid(padding=(0, 1))
    done.add_row(f"[green]Created {len(result.created)} files in[/green]", str(target))
    if result.venv_path:
        done.add_row("[green]Virtualenv[/green]", str(result.venv_path))
    console.print(Panel(done, title="[bold green]Done[/bold green]", border_style="green"))

    # markup=False so shell snippets like ".[dev]" are printed literally.
    console.print("\n[bold]Next steps:[/bold]")
    console.print(f"  cd {context.project_slug}", markup=False)
    if result.venv_path:
        console.print("  source .venv/bin/activate", markup=False)
    console.print('  pip install -e ".[dev]"', markup=False)
    console.print("  pytest\n", markup=False)


def _version_callback(value: bool) -> None:
    if value:
        # Plain print (not Rich) so the string stays machine-parsable.
        typer.echo(f"scaffld {__version__}")
        raise typer.Exit()


@app.callback()
def main_callback(
    version: bool = typer.Option(
        False, "--version", "-V", callback=_version_callback, is_eager=True
    ),
) -> None:
    """Scaffold new projects in seconds with a friendly TUI."""


def main() -> None:
    """Console-script entry point."""
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
