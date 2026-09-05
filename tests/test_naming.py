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


def test_package_name_avoids_python_keywords():
    # `src/class/` + `from class import ...` is a SyntaxError, so suffix it.
    assert naming.package_name("class") == "class_"
    assert naming.package_name("import") == "import_"
    assert naming.package_name("Lambda") == "lambda_"
    # Not a keyword: left alone.
    assert naming.package_name("classic") == "classic"


def test_words_transliterate_non_ascii():
    # Accented letters used to count as separators: "Cafe\u0301 Bu\u0301ho" -> caf_b_ho.
    assert naming.package_name("Caf\u00e9 B\u00faho") == "cafe_buho"
    assert naming.kebab_case("A\u00f1o Nuevo") == "ano-nuevo"
    assert naming.pascal_case("\u00e9cole normale") == "EcoleNormale"
    # Letters NFKD does not decompose come from the explicit map.
    assert naming.package_name("Stra\u00dfe") == "strasse"
    assert naming.package_name("\u0141\u00f3d\u017a") == "lodz"
