import pytest

from scaffld.render import TemplateError, evaluate_condition, render_string

CTX = {
    "project_name": "My Tool",
    "author": "Ada",
    "license": "MIT",
    "has_email": True,
    "empty": "",
}


def test_variable_substitution():
    assert render_string("Hi {{ author }}!", CTX) == "Hi Ada!"


def test_filters_chain():
    assert render_string("{{ project_name | snake }}", CTX) == "my_tool"
    assert render_string("{{ project_name | kebab | upper }}", CTX) == "MY-TOOL"


def test_unknown_variable_is_left_intact():
    # This is the GitHub Actions safety property.
    text = "run: echo ${{ matrix.python-version }} and {{ author }}"
    assert render_string(text, CTX) == "run: echo ${{ matrix.python-version }} and Ada"


def test_unknown_filter_raises():
    with pytest.raises(TemplateError):
        render_string("{{ author | nope }}", CTX)


def test_conditional_true_false():
    tpl = "{% if has_email %}yes{% else %}no{% endif %}"
    assert render_string(tpl, CTX) == "yes"
    assert render_string(tpl, {"has_email": False}) == "no"


def test_conditional_no_else():
    assert render_string("a{% if empty %}X{% endif %}b", CTX) == "ab"


def test_nested_conditionals():
    tpl = "{% if a %}[{% if b %}B{% else %}b{% endif %}]{% endif %}"
    assert render_string(tpl, {"a": True, "b": True}) == "[B]"
    assert render_string(tpl, {"a": True, "b": False}) == "[b]"
    assert render_string(tpl, {"a": False, "b": True}) == ""


def test_equality_conditions():
    assert render_string('{% if license == "MIT" %}m{% endif %}', CTX) == "m"
    assert render_string('{% if license != "MIT" %}x{% endif %}', CTX) == ""


def test_condition_helpers():
    assert evaluate_condition("not empty", CTX) is True
    assert evaluate_condition("has_email", CTX) is True


def test_unclosed_if_raises():
    with pytest.raises(TemplateError):
        render_string("{% if a %}oops", {"a": True})
