# {{ project_name }}

{{ description }}

## Install

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Usage

```python
from {{ package_name }} import greet

print(greet("{{ project_name }}"))
# -> Hello, {{ project_name }}!
```

## Development

```bash
pytest            # run the test suite
pre-commit install  # optional: format & lint on commit
```
{% if has_license %}
## License

{{ license }}. See [LICENSE](LICENSE).
{% endif %}
