"""{{ description }}"""

from __future__ import annotations

__version__ = "0.1.0"

__all__ = ["__version__", "greet"]


def greet(name: str = "world") -> str:
    """Return a friendly greeting.

    >>> greet("{{ project_name }}")
    'Hello, {{ project_name }}!'
    """
    return f"Hello, {name}!"
