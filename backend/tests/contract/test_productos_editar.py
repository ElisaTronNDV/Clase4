def _crear_producto(db_session, **overrides):
    from app.models.producto import Producto

    datos = dict(
        material="SAE_1010",
        espesor_mm=2.1,
        largo_mm=1200.0,
        ancho_mm=600.0,
        stock_fisico=10.0,
        stock_comprometido=0.0,
        punto_pedido=3.0,
    )
    datos.update(overrides)
    producto = Producto(**datos)
    db_session.add(producto)
    db_session.commit()
    db_session.refresh(producto)
    return producto


def _payload(**overrides):
    datos = {
        "material": "SAE_1010",
        "espesor_mm": 2.1,
        "largo_mm": 1200.0,
        "ancho_mm": 600.0,
        "stock_fisico": 15.0,
        "punto_pedido": 5.0,
    }
    datos.update(overrides)
    return datos


def test_editar_producto_200(client, auth_headers, db_session):
    producto = _crear_producto(db_session)

    resp = client.put(
        f"/api/productos/{producto.id}",
        headers=auth_headers,
        json=_payload(stock_fisico=20.0, punto_pedido=4.0),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == producto.id
    assert body["stock_fisico"] == 20.0
    assert body["punto_pedido"] == 4.0


def test_editar_producto_no_modifica_stock_comprometido(client, auth_headers, db_session):
    producto = _crear_producto(db_session, stock_comprometido=6.0)

    resp = client.put(
        f"/api/productos/{producto.id}",
        headers=auth_headers,
        json={**_payload(), "stock_comprometido": 999.0},
    )
    assert resp.status_code in (200, 422)
    if resp.status_code == 200:
        assert resp.json()["stock_comprometido"] == 6.0


def test_editar_producto_colision_exacta_409(client, auth_headers, db_session):
    _crear_producto(db_session, material="SAE_1020", largo_mm=900.0)
    producto = _crear_producto(db_session, material="SAE_1010", largo_mm=1200.0)

    resp = client.put(
        f"/api/productos/{producto.id}",
        headers=auth_headers,
        json=_payload(material="SAE_1020", largo_mm=900.0),
    )
    assert resp.status_code == 409


def test_editar_producto_sin_colision_si_alguna_dimension_difiere(client, auth_headers, db_session):
    _crear_producto(db_session, material="SAE_1020", largo_mm=900.0)
    producto = _crear_producto(db_session, material="SAE_1010", largo_mm=1200.0)

    resp = client.put(
        f"/api/productos/{producto.id}",
        headers=auth_headers,
        json=_payload(material="SAE_1020", largo_mm=901.0),
    )
    assert resp.status_code == 200


def test_editar_producto_permite_conservar_sus_propias_dimensiones(client, auth_headers, db_session):
    producto = _crear_producto(db_session)

    resp = client.put(
        f"/api/productos/{producto.id}",
        headers=auth_headers,
        json=_payload(stock_fisico=50.0),
    )
    assert resp.status_code == 200
    assert resp.json()["stock_fisico"] == 50.0


def test_editar_producto_inexistente_404(client, auth_headers, db_session):
    resp = client.put("/api/productos/999999", headers=auth_headers, json=_payload())
    assert resp.status_code == 404


def test_editar_producto_requiere_autenticacion_401(client, db_session):
    producto = _crear_producto(db_session)

    resp = client.put(f"/api/productos/{producto.id}", json=_payload())
    assert resp.status_code == 401
