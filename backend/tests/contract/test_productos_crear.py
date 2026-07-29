def _payload(**overrides):
    datos = {
        "material": "SAE_1010",
        "espesor_mm": 2.1,
        "largo_mm": 1200.0,
        "ancho_mm": 600.0,
        "stock_fisico": 10.0,
        "punto_pedido": 3.0,
    }
    datos.update(overrides)
    return datos


def test_crear_producto_201(client, auth_headers, db_session):
    resp = client.post("/api/productos", headers=auth_headers, json=_payload())
    assert resp.status_code == 201
    body = resp.json()
    assert "id" in body
    assert body["material"] == "SAE_1010"
    assert body["espesor_mm"] == 2.1
    assert body["largo_mm"] == 1200.0
    assert body["ancho_mm"] == 600.0
    assert body["stock_fisico"] == 10.0
    assert body["punto_pedido"] == 3.0
    assert body["stock_comprometido"] == 0


def test_crear_producto_asigna_id_secuencial(client, auth_headers, db_session):
    resp1 = client.post("/api/productos", headers=auth_headers, json=_payload())
    resp2 = client.post("/api/productos", headers=auth_headers, json=_payload(largo_mm=1300.0))
    assert resp1.status_code == 201 and resp2.status_code == 201
    id1, id2 = resp1.json()["id"], resp2.json()["id"]
    assert id2 == id1 + 1


def test_crear_producto_campo_faltante_422(client, auth_headers, db_session):
    payload = _payload()
    del payload["material"]
    resp = client.post("/api/productos", headers=auth_headers, json=payload)
    assert resp.status_code == 422


def test_crear_producto_duplicado_exacto_409(client, auth_headers, db_session):
    client.post("/api/productos", headers=auth_headers, json=_payload())
    resp = client.post("/api/productos", headers=auth_headers, json=_payload(stock_fisico=99.0))
    assert resp.status_code == 409


def test_crear_producto_no_duplicado_si_alguna_dimension_difiere(client, auth_headers, db_session):
    client.post("/api/productos", headers=auth_headers, json=_payload())
    resp = client.post("/api/productos", headers=auth_headers, json=_payload(largo_mm=1201.0))
    assert resp.status_code == 201


def test_crear_producto_requiere_autenticacion_401(client):
    resp = client.post("/api/productos", json=_payload())
    assert resp.status_code == 401
