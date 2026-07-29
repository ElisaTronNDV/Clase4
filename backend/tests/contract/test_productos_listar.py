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


def test_listar_productos_devuelve_todos(client, auth_headers, db_session):
    _crear_producto(db_session, material="SAE_1010", largo_mm=1200.0)
    _crear_producto(db_session, material="SAE_1020", largo_mm=900.0)

    resp = client.get("/api/productos", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    materiales = {p["material"] for p in body}
    assert materiales == {"SAE_1010", "SAE_1020"}
    for item in body:
        for campo in ("id", "material", "stock_fisico", "stock_comprometido", "alerta_stock_bajo"):
            assert campo in item


def test_listar_productos_alerta_stock_bajo_true_cuando_stock_disponible_menor_o_igual_a_punto_pedido(
    client, auth_headers, db_session
):
    _crear_producto(
        db_session,
        material="SAE_1010",
        stock_fisico=10.0,
        stock_comprometido=8.0,
        punto_pedido=3.0,
    )

    resp = client.get("/api/productos", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["alerta_stock_bajo"] is True


def test_listar_productos_alerta_stock_bajo_false_cuando_stock_disponible_mayor_a_punto_pedido(
    client, auth_headers, db_session
):
    _crear_producto(
        db_session,
        material="SAE_1010",
        stock_fisico=10.0,
        stock_comprometido=0.0,
        punto_pedido=3.0,
    )

    resp = client.get("/api/productos", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["alerta_stock_bajo"] is False


def test_listar_productos_alerta_stock_bajo_en_limite_exacto_es_true(client, auth_headers, db_session):
    _crear_producto(
        db_session,
        material="SAE_1010",
        stock_fisico=10.0,
        stock_comprometido=7.0,
        punto_pedido=3.0,
    )

    resp = client.get("/api/productos", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body[0]["alerta_stock_bajo"] is True


def test_listar_productos_sin_productos_devuelve_lista_vacia(client, auth_headers, db_session):
    resp = client.get("/api/productos", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


def test_listar_productos_requiere_autenticacion_401(client):
    resp = client.get("/api/productos")
    assert resp.status_code == 401
