# {{ project_name }}

{{ description }}

## Install

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Run

```bash
uvicorn {{ package_name }}.app:app --reload
# GET http://127.0.0.1:8000/health   -> {"status": "ok"}
# GET http://127.0.0.1:8000/greet/you -> {"message": "Hello, you!"}
```

## Development

```bash
pytest
```
{% if has_license %}
## License

{{ license }}. See [LICENSE](LICENSE).
{% endif %}
