from fastapi.testclient import TestClient


def test_health_returns_ok(client: TestClient):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_health_content_type_charset(client: TestClient):
    resp = client.get("/api/health")
    assert resp.headers["content-type"] == "application/json; charset=utf-8"


def test_health_idempotent(client: TestClient):
    first = client.get("/api/health")
    second = client.get("/api/health")
    third = client.get("/api/health")
    assert first.status_code == second.status_code == third.status_code == 200
    assert first.json() == second.json() == third.json() == {"status": "ok"}


def test_health_post_method_not_allowed(client: TestClient):
    resp = client.post("/api/health")
    assert resp.status_code == 405
    assert resp.json() == {
        "error": {"code": "INVALID_REQUEST", "message": "请求方法不支持"}
    }


def test_unknown_path_not_found(client: TestClient):
    resp = client.get("/api/undefined-path")
    assert resp.status_code == 404
    assert resp.json() == {
        "error": {"code": "INVALID_REQUEST", "message": "资源不存在"}
    }