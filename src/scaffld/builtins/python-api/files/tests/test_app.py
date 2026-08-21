from fastapi.testclient import TestClient

from {{ package_name }}.app import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_greet() -> None:
    response = client.get("/greet/{{ project_name }}")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello, {{ project_name }}!"}
