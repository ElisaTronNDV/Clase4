from unittest.mock import patch

from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app


def _cliente_como_lo_veria_un_http_real(db_session):
    """TestClient con raise_server_exceptions=False: refleja la respuesta que recibe un
    cliente HTTP real. Starlette's ServerErrorMiddleware relanza la excepción internamente
    para el logging del proceso servidor incluso después de enviar la respuesta al socket
    (comportamiento esperado, no un bug) — con raise_server_exceptions=True (default del
    fixture `client` compartido) esa excepción se propagaría como error de test en vez de
    devolver la respuesta.
    """

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app, raise_server_exceptions=False)
    return client


def test_excepcion_no_capturada_devuelve_500_generico_sin_detalle_interno(db_session):
    client = _cliente_como_lo_veria_un_http_real(db_session)
    with client:
        client.post(
            "/api/auth/registro", json={"email": "err@dyp.com", "password": "password123"}
        )
        token = client.post(
            "/api/auth/login", json={"email": "err@dyp.com", "password": "password123"}
        ).json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        with patch(
            "app.api.ordenes.extraer_propuesta",
            side_effect=RuntimeError("boom interno con detalle sensible"),
        ):
            resp = client.post(
                "/api/ordenes/extraer-pdf",
                headers=headers,
                files={"archivo": ("a.pdf", b"%PDF-1.4 fake", "application/pdf")},
            )

    app.dependency_overrides.clear()
    assert resp.status_code == 500
    assert resp.json() == {"detail": "Error interno del servidor"}
    assert "boom" not in resp.text
