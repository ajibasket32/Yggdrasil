from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def test_request_id_header_when_valid_id_supplied_preserves_id() -> None:
    request_id = str(uuid4())

    with TestClient(app) as client:
        response = client.get("/health/live", headers={"X-Request-ID": request_id})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == request_id


def test_request_id_header_when_invalid_id_supplied_replaces_id() -> None:
    with TestClient(app) as client:
        response = client.get("/health/live", headers={"X-Request-ID": "not-a-uuid"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] != "not-a-uuid"
