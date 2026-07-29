def _crear_orden_con_detalle(db_session, codigo_nest="NEST-000001", estado="vigente"):
    from app.models.orden_trabajo import OrdenTrabajo
    from app.models.pieza import Pieza
    from app.models.recorte_declarado import RecorteDeclarado

    orden = OrdenTrabajo(
        codigo_nest=codigo_nest,
        estado=estado,
        multiplicidad=2,
        espesor_mm=2.1,
        material="SAE_1010",
        largo_mm=1200.0,
        ancho_mm=600.0,
        tiempo_ejecucion_estimado="00:01:22",
    )
    db_session.add(orden)
    db_session.commit()
    db_session.refresh(orden)

    db_session.add(Pieza(orden_id=orden.id, descripcion="PC 1368 (CO) X3", cantidad=3))
    db_session.add(RecorteDeclarado(orden_id=orden.id, largo_mm=800.0, ancho_mm=400.0))
    db_session.commit()

    return orden


def test_buscar_orden_por_codigo_nest_200(client, auth_headers, db_session):
    orden = _crear_orden_con_detalle(db_session, codigo_nest="NEST-000042")

    resp = client.get(
        "/api/ordenes/buscar", headers=auth_headers, params={"codigo_nest": "NEST-000042"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == orden.id
    assert body["codigo_nest"] == "NEST-000042"
    assert body["estado"] == "vigente"
    assert body["material"] == "SAE_1010"
    assert len(body["piezas"]) == 1
    assert body["piezas"][0] == {"descripcion": "PC 1368 (CO) X3", "cantidad": 3}
    assert len(body["recortes"]) == 1
    assert body["recortes"][0]["largo_mm"] == 800.0
    assert body["recortes"][0]["ancho_mm"] == 400.0


def test_buscar_orden_codigo_inexistente_404(client, auth_headers, db_session):
    resp = client.get(
        "/api/ordenes/buscar", headers=auth_headers, params={"codigo_nest": "NEST-999999"}
    )
    assert resp.status_code == 404


def test_buscar_orden_requiere_autenticacion_401(client, db_session):
    _crear_orden_con_detalle(db_session)

    resp = client.get("/api/ordenes/buscar", params={"codigo_nest": "NEST-000001"})
    assert resp.status_code == 401
