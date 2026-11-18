from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.csrf import CSRF_HEADER, CSRF_VALUE, CSRFHeaderMiddleware
from app.core.errors import ConflictError, register_error_handlers


def _app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(CSRFHeaderMiddleware)
    register_error_handlers(app)

    @app.get("/conflict")
    async def conflict() -> None:
        raise ConflictError("Already exists", details={"field": "email"})

    @app.get("/boom")
    async def boom() -> None:
        raise RuntimeError("secret internals")

    @app.post("/write")
    async def write() -> dict[str, bool]:
        return {"ok": True}

    return app


def test_app_error_envelope() -> None:
    response = TestClient(_app()).get("/conflict")
    assert response.status_code == 409
    assert response.json() == {
        "error": {"code": "conflict", "message": "Already exists", "details": {"field": "email"}}
    }


def test_unhandled_error_hides_internals() -> None:
    response = TestClient(_app(), raise_server_exceptions=False).get("/boom")
    assert response.status_code == 500
    assert response.json() == {
        "error": {"code": "internal_error", "message": "Internal server error"}
    }
    assert "secret" not in response.text


def test_unknown_route_uses_envelope() -> None:
    response = TestClient(_app()).get("/missing")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_csrf_header_required_for_writes_only() -> None:
    client = TestClient(_app())
    assert client.post("/write").status_code == 403
    assert client.post("/write", headers={CSRF_HEADER: "wrong"}).status_code == 403
    assert client.post("/write", headers={CSRF_HEADER: CSRF_VALUE}).json() == {"ok": True}
    assert client.get("/conflict").status_code == 409  # GET is not blocked
