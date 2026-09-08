<!-- synced-from: 6e32af481bbec8ae4c9ac4504cc41f9be6f11fb5 -->
# scaffld

**English**: [README.md](README.md) · [Español](README.es.md)

![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![License: MIT](https://img.shields.io/badge/License-MIT-green)

**Crea un proyecto Python nuevo y completamente cableado en segundos — con una interfaz amable de terminal.**

`scaffld` genera un esqueleto de proyecto limpio (layout `src/`, tests, código tipado,
CI, pre-commit, licencia y, si quieres, un entorno virtual) a partir de plantillas
extensibles. Sin YAML de cookiecutter que memorizar, sin gimnasia de `{% raw %}` para
que los ficheros de GitHub Actions sobrevivan intactos — respondes cuatro preguntas y
te pones a escribir código.

```bash
pip install scaffld
scaffld new
```

> **Nota de idioma:** este README está en español; el resto de la documentación del
> repositorio, los mensajes de la CLI y los comentarios del código están en inglés.

## Qué hace

- **TUI interactiva** construida con [Rich](https://github.com/Textualize/rich) — eliges
  plantilla en una tabla, confirmas un resumen y ves aparecer el árbol de ficheros.
- **Con las pilas puestas** — cada proyecto sale con `pyproject.toml`, layout `src/`,
  tests de `pytest` que pasan desde el primer momento, una matriz de CI en GitHub
  Actions, un `.pre-commit-config.yaml`, una `LICENSE` de verdad y un `.gitignore`
  razonable.
- **Tres plantillas incluidas** — `python-lib`, `python-cli` y `python-api` (FastAPI).
- **Plantillas que no rompen GitHub Actions** — un motor propio y diminuto deja
  intactas las expresiones `${{ ... }}`, así que tus workflows se renderizan bien sin
  escapar nada.
- **Extensible** — dejas tu propia carpeta de plantillas en `~/.scaffld/templates` y
  aparece al instante. Una plantilla es un `template.toml` más un árbol `files/`.
- **Automatizable** — `--no-input` hace que `scaffld` funcione en CI y en Makefiles.
- **Entorno virtual sin configurar nada** — crea opcionalmente un `.venv` en el
  proyecto nuevo.

## Instalación

```bash
pip install scaffld
# o, desde un clon:
pip install -e ".[dev]"
```

`scaffld` está en PyPI, así que `pip install scaffld` funciona. Instalarlo desde un
clon requiere tener `git` en la máquina.

Necesita Python 3.9+. Dependencias en tiempo de ejecución: `typer` y `rich` (más
`tomli` en 3.9 y 3.10).

## Uso

Listar las plantillas disponibles:

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

Crear un proyecto. `scaffld new` sin argumentos lanza el flujo interactivo completo;
con flags te saltas las preguntas:

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

`scaffld show python-lib` imprime el árbol de ficheros que generaría una plantilla, sin
escribir nada en disco.

El proyecto generado es real y funciona de inmediato:

```console
$ cd weather-bot && pip install -e ".[dev]" && pytest -q
...                                                                        [100%]
3 passed in 0.01s

$ weather-bot Fernando
Hello, Fernando!
```

### Flags útiles

| Flag | Significado |
| --- | --- |
| `-t, --type` | Plantilla a usar (`scaffld list`). |
| `-a, --author` | Nombre del autor (por defecto `SCAFFLD_AUTHOR`, luego `git config user.name`, luego `$USER`). |
| `--email` | Email del autor (por defecto `SCAFFLD_EMAIL`, luego `git config user.email`). |
| `-d, --description` | Descripción del proyecto en una línea. |
| `-l, --license` | `MIT`, `BSD-3-Clause`, `ISC` o `none`. |
| `-o, --output` | Directorio donde crear el proyecto (por defecto, el actual). |
| `--python` | Versión mínima de Python del proyecto generado (`3.N` o `3.N.P`). |
| `--venv` / `--no-venv` | Crear un `.venv` en el proyecto nuevo. Activado por defecto. |
| `--no-input` | No preguntar nunca — falla si falta un valor obligatorio (ideal para CI). |
| `--force` | Escribir en un directorio que no está vacío. |

`scaffld -V` (o `--version`) imprime la versión y sale.

## Cómo funciona

Una plantilla es simplemente un directorio:

```
my-template/
├── template.toml        # nombre, tipo, descripción
└── files/               # el árbol que se renderiza
    ├── pyproject.toml
    ├── src/{{ package_name }}/__init__.py
    └── ...
```

Se renderizan **tanto el contenido de los ficheros como los segmentos de ruta**, así que
un directorio llamado literalmente `{{ package_name }}` acaba en disco como
`weather_bot/`.

El motor de renderizado es deliberadamente pequeño y tiene una propiedad que importa en
proyectos reales: **las expresiones `{{ ... }}` desconocidas se dejan intactas.** Eso
significa que un fichero de GitHub Actions puede contener `${{ matrix.python-version }}`
justo al lado de una variable de scaffld como `{{ project_name }}`, y solo se sustituye
la segunda — sin escapar nada. También admite filtros (`{{ project_name | snake }}`) y
condicionales anidables (`{% if has_license %}...{% endif %}`).

Las variables derivadas se calculan una vez y se mantienen coherentes: le das
`"Weather Bot"` y obtienes `package_name = weather_bot`, `project_slug = weather-bot`,
la licencia rellenada, el año y algunas más. Los nombres se transliteran primero a ASCII,
así que `"Café Búho"` da `cafe_buho` y no un `caf_b_ho` destrozado, y un nombre que
choca con una palabra reservada de Python recibe un guion bajo al final (`class` →
`class_`) para que el paquete siga siendo importable.

## Plantillas propias

Apunta `scaffld` a tus plantillas dejándolas en `~/.scaffld/templates/` (o en cualquier
directorio listado en la variable de entorno `SCAFFLD_TEMPLATES`). Una plantilla de
usuario que se llame igual que una incluida la eclipsa, así que puedes sobrescribir las
que vienen de serie. Variables disponibles: `project_name`, `package_name`,
`project_slug`, `author`, `author_email`, `description`, `license`, `python_version` y
`year`.

## Desarrollo

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Parte del ecosistema ferinazumaDEV

`scaffld` es una de una familia de herramientas pequeñas y enfocadas de código abierto
que construyo y mantengo. Si te ha ahorrado tiempo de montar un proyecto, algunos de
sus hermanos atacan problemas vecinos con el mismo espíritu práctico:

- [The GEO Handbook](https://github.com/ferinazumaDEV/generative-engine-optimization-handbook) — la referencia abierta sobre cómo conseguir que los motores de respuesta con IA (ChatGPT, Perplexity, Google AI Overviews, Gemini, Copilot) citen tu contenido.
- [politeclient](https://github.com/ferinazumaDEV/politeclient) — un cliente HTTP cuidadoso y bien educado para Python: reintentos con backoff, límite de peticiones por host, caché y paginación.
- [typedout](https://github.com/ferinazumaDEV/typedout) — salida estructurada fiable desde OpenAI y Anthropic, con una interfaz de proveedor para los demás: JSON validado contra esquema, con reparación tolerante y reintentos.
- [webhook-replay](https://github.com/ferinazumaDEV/webhook-replay) — captura un webhook una vez y reprodúcelo contra tu aplicación local tantas veces como necesites.
- Hub y escritura: [zentimes.es](https://zentimes.es).

Por [ferinazumaDEV](https://github.com/ferinazumaDEV).

## Licencia

MIT — ver [LICENSE](LICENSE).

---

Hecho por Fernando ([@ferinazumaDEV](https://github.com/ferinazumaDEV)).
