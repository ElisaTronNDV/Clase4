def _crear_producto(db_session, **overrides):
    from app.models.producto import Producto

    datos = dict(
        material="SAE_1010",
        espesor_mm=2.1,
        largo_mm=1200.0,
        ancho_mm=600.0,
        stock_fisico=50.0,
        stock_comprometido=0.0,
        punto_pedido=5.0,
    )
    datos.update(overrides)
    producto = Producto(**datos)
    db_session.add(producto)
    db_session.commit()
    db_session.refresh(producto)
    return producto


def _crear_orden(db_session, producto_comprometido_id=None, multiplicidad=2, estado="vigente", **overrides):
    from app.models.orden_trabajo import OrdenTrabajo

    datos = dict(
        codigo_nest="NEST-000001",
        estado=estado,
        multiplicidad=multiplicidad,
        espesor_mm=2.1,
        material="SAE_1010",
        largo_mm=1200.0,
        ancho_mm=600.0,
        tiempo_ejecucion_estimado="00:01:22",
        producto_comprometido_id=producto_comprometido_id,
    )
    datos.update(overrides)
    orden = OrdenTrabajo(**datos)
    db_session.add(orden)
    db_session.commit()
    db_session.refresh(orden)
    return orden


def _agregar_recorte(db_session, orden, largo_mm, ancho_mm):
    from app.models.recorte_declarado import RecorteDeclarado

    recorte = RecorteDeclarado(orden_id=orden.id, largo_mm=largo_mm, ancho_mm=ancho_mm)
    db_session.add(recorte)
    db_session.commit()
    db_session.refresh(recorte)
    return recorte


def test_cerrar_orden_descuenta_stock_igual_a_multiplicidad_200(client, auth_headers, db_session):
    producto = _crear_producto(db_session, stock_fisico=50.0, stock_comprometido=2.0)
    orden = _crear_orden(db_session, producto_comprometido_id=producto.id, multiplicidad=2)

    resp = client.post(f"/api/ordenes/{orden.id}/cerrar", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == orden.id
    assert body["estado"] == "cerrada"
    assert body["closed_at"] is not None

    db_session.refresh(producto)
    assert producto.stock_fisico == 48.0
    assert producto.stock_comprometido == 0.0

    db_session.refresh(orden)
    assert orden.estado == "cerrada"
    assert orden.closed_at is not None


def test_cerrar_orden_da_de_alta_producto_para_recorte_sin_coincidencia(
    client, auth_headers, db_session
):
    producto_comprometido = _crear_producto(db_session, stock_fisico=50.0, stock_comprometido=2.0)
    orden = _crear_orden(
        db_session,
        producto_comprometido_id=producto_comprometido.id,
        multiplicidad=2,
        material="SAE_1010",
        espesor_mm=2.1,
    )
    recorte = _agregar_recorte(db_session, orden, largo_mm=800.0, ancho_mm=400.0)

    resp = client.post(f"/api/ordenes/{orden.id}/cerrar", headers=auth_headers)
    assert resp.status_code == 200

    from app.models.producto import Producto

    nuevo_producto = (
        db_session.query(Producto)
        .filter(
            Producto.material == "SAE_1010",
            Producto.largo_mm == 800.0,
            Producto.ancho_mm == 400.0,
        )
        .first()
    )
    assert nuevo_producto is not None
    assert nuevo_producto.espesor_mm == 2.1
    assert nuevo_producto.stock_fisico == 1.0

    db_session.refresh(recorte)
    assert recorte.producto_resultante_id == nuevo_producto.id


def test_cerrar_orden_incrementa_producto_existente_para_recorte_con_coincidencia(
    client, auth_headers, db_session
):
    producto_comprometido = _crear_producto(db_session, stock_fisico=50.0, stock_comprometido=2.0)
    producto_recorte = _crear_producto(
        db_session,
        material="SAE_1010",
        espesor_mm=2.1,
        largo_mm=800.0,
        ancho_mm=400.0,
        stock_fisico=5.0,
        stock_comprometido=0.0,
        punto_pedido=1.0,
    )
    orden = _crear_orden(db_session, producto_comprometido_id=producto_comprometido.id, multiplicidad=2)
    recorte = _agregar_recorte(db_session, orden, largo_mm=800.0, ancho_mm=400.0)

    resp = client.post(f"/api/ordenes/{orden.id}/cerrar", headers=auth_headers)
    assert resp.status_code == 200

    db_session.refresh(producto_recorte)
    assert producto_recorte.stock_fisico == 6.0

    db_session.refresh(recorte)
    assert recorte.producto_resultante_id == producto_recorte.id


def test_cerrar_orden_ya_cerrada_409(client, auth_headers, db_session):
    producto = _crear_producto(db_session)
    orden = _crear_orden(db_session, producto_comprometido_id=producto.id, estado="cerrada")

    resp = client.post(f"/api/ordenes/{orden.id}/cerrar", headers=auth_headers)
    assert resp.status_code == 409


def test_cerrar_orden_inexistente_404(client, auth_headers):
    resp = client.post("/api/ordenes/999999/cerrar", headers=auth_headers)
    assert resp.status_code == 404


def test_cerrar_orden_requiere_autenticacion_401(client, db_session):
    producto = _crear_producto(db_session)
    orden = _crear_orden(db_session, producto_comprometido_id=producto.id)

    resp = client.post(f"/api/ordenes/{orden.id}/cerrar")
    assert resp.status_code == 401
