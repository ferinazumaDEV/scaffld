# Security policy

## Supported versions

Only the latest release is supported. Fixes land on `main`; there are no backport branches.

| Version | Supported |
| --- | --- |
| 0.1.x | yes |
| older | no |

## Reporting a problem

Please report privately first.

1. Preferred: GitHub's private vulnerability reporting on this repository — **Security → Report a
   vulnerability** ([direct link](https://github.com/ferinazumaDEV/scaffld/security/advisories/new)).
2. If that form is not available to you,
   [open an issue](https://github.com/ferinazumaDEV/scaffld/issues) saying only that you have a
   security report and how to reach you. **Do not put exploit details in a public issue** — a private
   channel will be arranged from there.

Expect a first reply within a week. Small project, spare time; no formal SLA and no bug bounty.

Useful to include: the scaffld and Python versions, which template, a minimal reproduction, and what
an attacker gains.

## A template is a trust decision

This is the thing to understand before installing someone else's template.

scaffld templates are **data, not code**: they are files rendered against a variable set. There are
**no post-generation hooks** — nothing in a template is executed, which is the main difference from
cookiecutter and the main reason there is no sandbox here.

But a template still **writes files into your project**, and files get executed later by other tools.
A hostile template does not need a hook when it can ship a `conftest.py` that runs on your next
`pytest`, a `.github/workflows/*.yml` that runs on your next push, or a `setup.py` that runs on
install. So: **read a template before you use it, the same way you would read a script.**

Templates are discovered from, in order:

- the built-ins shipped inside the package,
- your user template directory, `~/.scaffld/templates`,
- any path in the **`SCAFFLD_TEMPLATES`** environment variable (`PATH`-style, `os.pathsep`-separated),
- any directory passed explicitly on the command line.

Anything that can write to those locations, or set that variable, chooses what scaffld writes.

## What scaffld will not do

- **It will not escape the target directory.** Path segments come from template variables, so
  `{{ author }}` could render to `../../escaped`. Every rendered segment is checked: any segment that
  is `..` or that contains a path separator is rejected by name, before anything is written.
- **It will not overwrite your work.** The target directory must be empty, and every individual file
  refuses to clobber an existing one, unless you pass `--force`.
- **It runs no shell.** The only external command is `git config --get <key>`, invoked as an argument
  list (never `shell=True`) with a 2-second timeout, and it only reads.

## What ends up in the files it writes

scaffld fills the author fields from **your git config** — `user.name` and `user.email` — unless you
override them (`--author`, `--email`, or the `SCAFFLD_EMAIL` environment variable). Those values are
written into the generated `LICENSE`, `pyproject.toml` and docs, so **the email address in your git
config is the one you are about to publish**. Check it before generating a project you intend to push,
particularly on a shared or work machine.

## The virtualenv step

By default `scaffld new` creates a `.venv` in the generated project. That runs Python's own `venv`
module locally and installs nothing from the network. Pass `--no-venv` to skip it.

## Out of scope

Reports that a caller can hurt themselves — installing a template they did not read, pointing
`SCAFFLD_TEMPLATES` at a world-writable directory, or using `--force` over files that mattered — are
documentation issues rather than vulnerabilities. Still welcome as issues.
