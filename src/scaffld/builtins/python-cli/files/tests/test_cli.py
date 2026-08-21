from {{ package_name }}.cli import build_parser, main


def test_default_greeting(capsys) -> None:
    assert main([]) == 0
    assert capsys.readouterr().out.strip() == "Hello, world!"


def test_named_greeting(capsys) -> None:
    assert main(["scaffld"]) == 0
    assert capsys.readouterr().out.strip() == "Hello, scaffld!"


def test_parser_builds() -> None:
    assert build_parser().prog == "{{ project_slug }}"
