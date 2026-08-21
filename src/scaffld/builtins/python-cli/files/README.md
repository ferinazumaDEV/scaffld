# {{ project_name }}

{{ description }}

## Install

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Usage

```bash
{{ project_slug }} World
# -> Hello, World!

{{ project_slug }} --version
```

## Development

```bash
pytest
```
{% if has_license %}
## License

{{ license }}. See [LICENSE](LICENSE).
{% endif %}
