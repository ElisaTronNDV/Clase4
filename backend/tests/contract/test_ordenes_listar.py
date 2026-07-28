from datetime import datetime, timezone


def _crear_orden(db_session, codigo_nest, estado="vigente", **overrides):
    from app.models.orden_trabajo import OrdenTrabajo

    datos = dict(
        codigo_nest=codigo_nest,
        estado=estado,
        multiplicidad=1,
        espesor_mm=2.1,
        material="SAE_1010",
        largo_mm=1200.0,
        ancho_mm=600.0,
        tiempo_ejecucion_estimado="00:01:22",
    )
    datos.update(overrides)
    if estado == "cerrada" and "closed_at" not in overrides:
        datos["closed_at"] = datetime.now(timezone.utc)
    orden = OrdenTrabajo(**datos)
    db_session.add(orden)
    db_session.commit()
    db_session.refresh(orden)
    return orden


def test_listar_ordenes_sin_filtros_devuelve_todas(client, auth_headers, db_session):
    _crear_orden(db_session, "NEST-000001", estado="vigente")
    _crear_orden(db_session, "NEST-000002", estado="cerrada")

    resp = client.get("/api/ordenes", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    codigos = {o["codigo_nest"] for o in body}
    assert codigos == {"NEST-000001", "NEST-000002"}
    for item in body:
        for campo in ("id", "codigo_nest", "estado", "material"):
            assert campo in item


def test_listar_ordenes_filtra_por_estado(client, auth_headers, db_session):
    _crear_orden(db_session, "NEST-000001", estado="vigente")
    _crear_orden(db_session, "NEST-000002", estado="cerrada")

    resp = client.get("/api/ordenes", headers=auth_headers, params={"estado": "vigente"})
    assert resp.status_code == 200
    body = resp.json()
    assert {o["codigo_nest"] for o in body} == {"NEST-000001"}
    assert all(o["estado"] == "vigente" for o in body)


def test_listar_ordenes_busca_por_nest_parcial(client, auth_headers, db_session):
    _crear_orden(db_session, "NEST-000123", estado="vigente")
    _crear_orden(db_session, "NEST-000999", estado="vigente")

    resp = client.get("/api/ordenes", headers=auth_headers, params={"nest": "0123"})
    assert resp.status_code == 200
    body = resp.json()
    assert {o["codigo_nest"] for o in body} == {"NEST-000123"}


def test_listar_ordenes_filtros_combinables(client, auth_headers, db_session):
    _crear_orden(db_session, "NEST-000123", estado="vigente")
    _crear_orden(db_session, "NEST-000124", estado="cerrada")
    _crear_orden(db_session, "NEST-000999", estado="vigente")

    resp = client.get(
        "/api/ordenes", headers=auth_headers, params={"estado": "vigente", "nest": "0012"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert {o["codigo_nest"] for o in body} == {"NEST-000123"}


def test_listar_ordenes_sin_resultados_devuelve_lista_vacia(client, auth_headers, db_session):
    _crear_orden(db_session, "NEST-000001", estado="vigente")

    resp = client.get("/api/ordenes", headers=auth_headers, params={"nest": "999999"})
    assert resp.status_code == 200
    assert resp.json() == []


def test_listar_ordenes_requiere_autenticacion_401(client):
    resp = client.get("/api/ordenes")
    assert resp.status_code == 401
