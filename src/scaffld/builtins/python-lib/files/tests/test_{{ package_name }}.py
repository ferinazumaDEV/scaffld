from {{ package_name }} import greet


def test_greet_default() -> None:
    assert greet() == "Hello, world!"


def test_greet_name() -> None:
    assert greet("{{ project_name }}") == "Hello, {{ project_name }}!"
