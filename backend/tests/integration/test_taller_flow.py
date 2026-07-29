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


def _crear_orden_vigente(db_session, producto_comprometido_id, multiplicidad=2):
    from app.models.orden_trabajo import OrdenTrabajo
    from app.models.pieza import Pieza
    from app.models.recorte_declarado import RecorteDeclarado

    orden = OrdenTrabajo(
        codigo_nest="NEST-000777",
        estado="vigente",
        multiplicidad=multiplicidad,
        espesor_mm=2.1,
        material="SAE_1010",
        largo_mm=1200.0,
        ancho_mm=600.0,
        tiempo_ejecucion_estimado="00:01:22",
        producto_comprometido_id=producto_comprometido_id,
    )
    db_session.add(orden)
    db_session.commit()
    db_session.refresh(orden)

    db_session.add(Pieza(orden_id=orden.id, descripcion="PC 1368 (CO) X3", cantidad=3))
    # Recorte sin coincidencia (da de alta un producto nuevo al cerrar).
    db_session.add(RecorteDeclarado(orden_id=orden.id, largo_mm=800.0, ancho_mm=400.0))
    # Recorte con coincidencia (incrementa un producto existente al cerrar).
    db_session.add(RecorteDeclarado(orden_id=orden.id, largo_mm=300.0, ancho_mm=150.0))
    db_session.commit()

    return orden


def test_flujo_completo_escanear_mostrar_cerrar_y_verificar_descuento_y_recortes(
    client, auth_headers, db_session
):
    producto_comprometido = _crear_producto(db_session, stock_fisico=50.0, stock_comprometido=2.0)
    producto_recorte_existente = _crear_producto(
        db_session,
        material="SAE_1010",
        espesor_mm=2.1,
        largo_mm=300.0,
        ancho_mm=150.0,
        stock_fisico=3.0,
        stock_comprometido=0.0,
        punto_pedido=1.0,
    )
    orden = _crear_orden_vigente(db_session, producto_comprometido.id, multiplicidad=2)

    # 1. Escanear/ingresar el NEST y mostrar la orden asociada (FR-018).
    resp_buscar = client.get(
        "/api/ordenes/buscar", headers=auth_headers, params={"codigo_nest": "NEST-000777"}
    )
    assert resp_buscar.status_code == 200
    orden_encontrada = resp_buscar.json()
    assert orden_encontrada["id"] == orden.id
    assert orden_encontrada["estado"] == "vigente"
    assert len(orden_encontrada["piezas"]) == 1
    assert len(orden_encontrada["recortes"]) == 2

    # 2. Finalizar la orden en Taller (FR-019).
    resp_cerrar = client.post(f"/api/ordenes/{orden.id}/cerrar", headers=auth_headers)
    assert resp_cerrar.status_code == 200
    assert resp_cerrar.json()["estado"] == "cerrada"

    # 3. El stock comprometido/físico se descuenta en la multiplicidad (FR-020).
    db_session.refresh(producto_comprometido)
    assert producto_comprometido.stock_fisico == 48.0
    assert producto_comprometido.stock_comprometido == 0.0

    # 4. El recorte sin coincidencia da de alta un producto nuevo con stock 1 (FR-022).
    from app.models.producto import Producto

    producto_nuevo = (
        db_session.query(Producto)
        .filter(
            Producto.material == "SAE_1010",
            Producto.largo_mm == 800.0,
            Producto.ancho_mm == 400.0,
        )
        .first()
    )
    assert producto_nuevo is not None
    assert producto_nuevo.stock_fisico == 1.0

    # 5. El recorte con coincidencia incrementa el stock del producto existente (FR-023).
    db_session.refresh(producto_recorte_existente)
    assert producto_recorte_existente.stock_fisico == 4.0

    # 6. La orden ahora figura como cerrada al volver a buscarla.
    resp_buscar_final = client.get(
        "/api/ordenes/buscar", headers=auth_headers, params={"codigo_nest": "NEST-000777"}
    )
    assert resp_buscar_final.status_code == 200
    assert resp_buscar_final.json()["estado"] == "cerrada"

    # 7. No se puede volver a cerrar una orden ya cerrada.
    resp_cerrar_de_nuevo = client.post(f"/api/ordenes/{orden.id}/cerrar", headers=auth_headers)
    assert resp_cerrar_de_nuevo.status_code == 409
