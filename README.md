# scaffld

[English](README.md) · **Español**: [README.es.md](README.es.md)

![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![License: MIT](https://img.shields.io/badge/License-MIT-green)

**Scaffold a new, fully-wired Python project in seconds — with a friendly terminal UI.**

`scaffld` generates a clean project skeleton (src layout, tests, typed code, CI,
pre-commit, license, and an optional virtualenv) from extensible templates. No
cookiecutter YAML to memorize, no `{% raw %}` gymnastics to keep GitHub Actions
files intact — just answer a few prompts and start writing code.

```bash
pip install scaffld
scaffld new
```

## Features

- **Interactive TUI** built with [Rich](https://github.com/Textualize/rich) — pick a
  template from a table, confirm a summary, watch the file tree appear.
- **Batteries included** — every project ships with `pyproject.toml`, a `src/` layout,
  `pytest` tests that pass out of the box, a GitHub Actions matrix CI, a
  `.pre-commit-config.yaml`, a real `LICENSE`, and a sensible `.gitignore`.
- **Three built-in templates** — `python-lib`, `python-cli`, and `python-api` (FastAPI).
- **GitHub-Actions-safe templating** — a tiny custom engine leaves `${{ ... }}`
  expressions untouched, so your workflow files render correctly with zero escaping.
- **Extensible** — drop your own template folder in `~/.scaffld/templates` and it shows
  up instantly. Templates are just a `template.toml` plus a `files/` tree.
- **Scriptable** — `--no-input` makes `scaffld` behave in CI and Makefiles.
- **Zero-config virtualenv** — optionally creates `.venv` for the new project.

## Install

```bash
pip install scaffld
# or, from a clone:
pip install -e ".[dev]"
```

`scaffld` is on PyPI, so `pip install scaffld` works. Installing from a clone
instead needs `git` on your machine.

Requires Python 3.9+. Runtime dependencies: `typer` and `rich` (plus `tomli` on 3.9/3.10).

## Usage

List the available templates:

```console
$ scaffld list
                              Available templates
┏━━━┳━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ # ┃ Template   ┃ Kind    ┃ Description                                       ┃
┡━━━╇━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 1 │ python-api │ api     │ FastAPI service with a health route, typed        │
│   │            │         │ handlers, and CI.                                 │
│ 2 │ python-cli │ cli     │ Zero-dependency argparse CLI with a               │
│   │            │         │ console-script entry point.                       │
│ 3 │ python-lib │ library │ Importable Python library: src/ layout, typed     │
│   │            │         │ API, tests, and CI.                               │
└───┴────────────┴─────────┴───────────────────────────────────────────────────┘
```

Create a project. Run `scaffld new` with no arguments for the full interactive flow,
or pass flags to skip the prompts:

```console
$ scaffld new "Weather Bot" -t python-cli -a "Ada Lovelace" -d "A tiny weather CLI." --no-input --no-venv
weather-bot/
├── .github/
│   └── workflows/
│       └── ci.yml
├── .gitignore
├── .pre-commit-config.yaml
├── LICENSE
├── README.md
├── pyproject.toml
├── src/
│   └── weather_bot/
│       ├── __init__.py
│       └── cli.py
└── tests/
    └── test_cli.py
╭──────────────────────────────────── Done ────────────────────────────────────╮
│ Created 9 files in /tmp/weather-bot                                          │
╰──────────────────────────────────────────────────────────────────────────────╯

Next steps:
  cd weather-bot
  pip install -e ".[dev]"
  pytest
```

`scaffld show python-lib` prints the file tree a template would generate, without
writing anything to disk.

The generated project is real and works immediately:

```console
$ cd weather-bot && pip install -e ".[dev]" && pytest -q
...                                                                        [100%]
3 passed in 0.01s

$ weather-bot Fernando
Hello, Fernando!
```

### Useful flags

| Flag | Meaning |
| --- | --- |
| `-t, --type` | Template to use (`scaffld list`). |
| `-a, --author` | Author name (defaults to `SCAFFLD_AUTHOR`, then `git config user.name`, then `$USER`). |
| `--email` | Author email (defaults to `SCAFFLD_EMAIL`, then `git config user.email`). |
| `-d, --description` | One-line project description. |
| `-l, --license` | `MIT`, `BSD-3-Clause`, `ISC`, or `none`. |
| `-o, --output` | Directory to create the project in (defaults to the current directory). |
| `--python` | Minimum Python version for the generated project (`3.N` or `3.N.P`). |
| `--venv` / `--no-venv` | Create a `.venv` in the new project. On by default. |
| `--no-input` | Never prompt — fail if a required value is missing (great for CI). |
| `--force` | Write into a non-empty directory. |

`scaffld -V` (or `--version`) prints the version and exits.

## How it works

A template is just a directory:

```
my-template/
├── template.toml        # name, kind, description
└── files/               # the tree that gets rendered
    ├── pyproject.toml
    ├── src/{{ package_name }}/__init__.py
    └── ...
```

Both **file contents and path segments** are rendered, so a directory literally named
`{{ package_name }}` becomes `weather_bot/` on disk.

The rendering engine is deliberately small and has one property that matters for real
projects: **unknown `{{ ... }}` expressions are left untouched.** That means a GitHub
Actions file can contain `${{ matrix.python-version }}` right next to a scaffld variable
like `{{ project_name }}`, and only the latter is substituted — no escaping required. It
also supports filters (`{{ project_name | snake }}`) and nestable conditionals
(`{% if has_license %}...{% endif %}`).

Derived variables are computed once and kept consistent: give it `"Weather Bot"` and you
get `package_name = weather_bot`, `project_slug = weather-bot`, a filled-in license, the
year, and more. Names are transliterated to ASCII first, so `"Café Búho"` yields
`cafe_buho` rather than a shredded `caf_b_ho`, and a name that collides with a Python
keyword gets a trailing underscore (`class` → `class_`) so the package stays importable.

## Custom templates

Point `scaffld` at your own templates by dropping them in `~/.scaffld/templates/`
(or any directory listed in the `SCAFFLD_TEMPLATES` environment variable). A user
template that shares a name with a built-in one shadows it, so you can override the
defaults. Available variables include `project_name`, `package_name`, `project_slug`,
`author`, `author_email`, `description`, `license`, `python_version`, and `year`.

## Development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Part of the ferinazumaDEV ecosystem

`scaffld` is one of a family of small, focused open-source tools I build and maintain. If it saved you some project-setup time, a few of the sibling projects tackle neighbouring problems in the same practical, batteries-included spirit.

- [The GEO Handbook](https://github.com/ferinazumaDEV/generative-engine-optimization-handbook) — the open reference on getting content cited by AI answer engines (ChatGPT, Perplexity, Google AI Overviews, Gemini, Copilot).
- [politeclient](https://github.com/ferinazumaDEV/politeclient) — a careful, well-behaved HTTP client for Python: retries with backoff, per-host rate-limiting, caching, and pagination.
- [typedout](https://github.com/ferinazumaDEV/typedout) — reliable structured output from OpenAI and Anthropic, with a provider interface for others: schema-validated JSON with tolerant repair and retries.
- [webhook-replay](https://github.com/ferinazumaDEV/webhook-replay) — capture a webhook once, then replay it at your local app as many times as you need.
- Hub & writing: [zentimes.es](https://zentimes.es).

By [ferinazumaDEV](https://github.com/ferinazumaDEV).

## License

MIT — see [LICENSE](LICENSE).

---

Built by Fernando ([@ferinazumaDEV](https://github.com/ferinazumaDEV)).
