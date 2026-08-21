from scaffld import naming


def test_snake_case():
    assert naming.snake_case("My Cool-Lib") == "my_cool_lib"
    assert naming.snake_case("myCoolLib") == "my_cool_lib"
    assert naming.snake_case("HTTPServer2") == "http_server2"


def test_kebab_case():
    assert naming.kebab_case("My Cool Lib") == "my-cool-lib"
    assert naming.kebab_case("already_snake") == "already-snake"


def test_pascal_and_camel():
    assert naming.pascal_case("my cool lib") == "MyCoolLib"
    assert naming.camel_case("my cool lib") == "myCoolLib"
    assert naming.camel_case("") == ""


def test_package_name_edge_cases():
    assert naming.package_name("2fast") == "_2fast"
    assert naming.package_name("!!!") == "package"
    assert naming.package_name("Data Loader") == "data_loader"
