def test_obtener_configuracion_devuelve_default_1_0(client, auth_headers, db_session):
    resp = client.get("/api/configuracion", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == {"margen_tolerancia_mm": 1.0}


def test_obtener_configuracion_requiere_autenticacion_401(client):
    resp = client.get("/api/configuracion")
    assert resp.status_code == 401
