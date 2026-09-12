# Changelog

Notable changes, newest first. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- **Generated projects no longer break on quotes, backslashes or newlines in the
  author or description.** Both fields were interpolated into `pyproject.toml`
  and into Python source as plain text, so any character that is special in the
  destination grammar produced a project that would not parse. An author called
  `Ana "AI"` was enough to yield `authors = [{ name = "Ana "AI"" }]` and a
  `TOMLDecodeError`. Nine of twelve template/input combinations failed; the
  existing end-to-end test passed throughout, because it generates with one
  benign name.

  Templates now choose an escaper for the grammar they are writing into:
  `{{ description | toml }}` inside a TOML basic string, `{{ description | py }}`
  inside a Python literal, and neither in Markdown body text. Both filters are
  public and round-trip tested.

Reported in the external audit of the `2026.09.0` ecosystem snapshot as F03.

## [0.1.1] — 2026-09-06

A release so that what you install contains the guards, not just `main`.

`0.1.0` predates the repository-hygiene incident and its fix. The published
package was never affected — the tag came before the mistake, and the sdist and
wheel are 31 KB and 32 KB — but a user installing scaffld should get the version
that cannot repeat it.

### Added

- **A CI guard against committing a virtualenv.** A `.v/` directory reached
  `main` on 2026-09-06: 1,380 files and 467,125 lines, which was 95% of
  everything the repository tracked. `.gitignore` listed `.venv/`, `venv/` and
  `env/` but not that spelling.

  `.gitignore` could not have prevented it and cannot prevent the next one — it
  does nothing for a path already tracked, and nothing against `git add -f`. So
  the guard asks git what it is *actually tracking* and fails on the markers of
  an environment (`pyvenv.cfg`, `site-packages/`, `dist-packages/`, and
  `bin|lib|Scripts` under a venv-shaped directory) whatever the directory was
  called. A second step caps the tracked-file count as a backstop.

  It was checked against the real thing before being trusted: it passes on the
  clean tree and finds 1,379 paths in the broken one.
- **CI on every push and pull request** — the suite across Python 3.9–3.12, and
  a job that generates a project from each of the three templates, installs it,
  runs its tests and builds a wheel. A scaffolder whose output does not build is
  broken however green its own unit tests are.
- **`SECURITY.md`**, including the part that matters for a scaffolder: templates
  are data, not code — there are no post-generation hooks — but a template still
  writes files that other tools execute later, so read one before you use it.
- This changelog.

### Changed

- `actions/checkout` and `actions/setup-python` moved to v7; the runs no longer
  warn about a deprecated Node runtime.

### Note

The history was deliberately not rewritten. That would change every hash after
the commit and break clones and links, to fix something that lives in the
working tree rather than in the object store. `main` is clean going forward.

## [0.1.0] — 2026-09-05

First tagged release and first publication to PyPI.

[0.1.1]: https://github.com/ferinazumaDEV/scaffld/releases
[0.1.0]: https://github.com/ferinazumaDEV/scaffld/releases/tag/v0.1.0
