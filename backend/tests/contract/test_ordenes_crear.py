import re

CODIGO_NEST_RE = re.compile(r"^NEST-\d{6}$")


def _orden_payload(**overrides):
    payload = {
        "multiplicidad": 2,
        "espesor_mm": 2.1,
        "material": "SAE_1010",
        "largo_mm": 1200.0,
        "ancho_mm": 600.0,
        "tiempo_ejecucion_estimado": "00:01:22",
        "piezas": [{"descripcion": "PC 1368 (CO) X3", "cantidad": 3}],
        "recortes": [{"largo_mm": 800.0, "ancho_mm": 400.0}],
    }
    payload.update(overrides)
    return payload


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


def _contar_filas(db_session):
    from app.models.orden_trabajo import OrdenTrabajo
    from app.models.pieza import Pieza
    from app.models.producto import Producto
    from app.models.recorte_declarado import RecorteDeclarado

    return {
        "ordenes": db_session.query(OrdenTrabajo).count(),
        "piezas": db_session.query(Pieza).count(),
        "recortes": db_session.query(RecorteDeclarado).count(),
        "productos": db_session.query(Producto).count(),
    }


def _busca_clave(obj, clave):
    if isinstance(obj, dict):
        if clave in obj:
            return True
        return any(_busca_clave(v, clave) for v in obj.values())
    if isinstance(obj, list):
        return any(_busca_clave(v, clave) for v in obj)
    return False


def test_crear_orden_compromete_stock_igual_a_multiplicidad_201(client, auth_headers, db_session):
    producto = _crear_producto(db_session, stock_fisico=50.0, punto_pedido=5.0)

    resp = client.post(
        "/api/ordenes", headers=auth_headers, json=_orden_payload(multiplicidad=2)
    )
    assert resp.status_code == 201
    body = resp.json()
    assert CODIGO_NEST_RE.match(body["codigo_nest"])
    assert body["estado"] == "vigente"
    assert body["producto_comprometido"]["id"] == producto.id
    assert body["producto_comprometido"]["creado_automaticamente"] is False
    assert body["alerta_stock_bajo"] is False

    db_session.refresh(producto)
    assert producto.stock_comprometido == 2.0
    assert producto.stock_fisico == 50.0
    assert _contar_filas(db_session) == {
        "ordenes": 1,
        "piezas": 1,
        "recortes": 1,
        "productos": 1,
    }


def test_crear_orden_codigo_nest_secuencial(client, auth_headers, db_session):
    _crear_producto(db_session)

    resp1 = client.post("/api/ordenes", headers=auth_headers, json=_orden_payload())
    resp2 = client.post("/api/ordenes", headers=auth_headers, json=_orden_payload())
    assert resp1.status_code == 201
    assert resp2.status_code == 201
    assert resp1.json()["codigo_nest"] != resp2.json()["codigo_nest"]
    assert int(resp2.json()["codigo_nest"].split("-")[1]) > int(
        resp1.json()["codigo_nest"].split("-")[1]
    )


def test_crear_orden_sin_coincidencia_advertencia_404(client, auth_headers, db_session):
    resp = client.post(
        "/api/ordenes",
        headers=auth_headers,
        json=_orden_payload(material="INOX", largo_mm=999.0, ancho_mm=999.0),
    )
    assert resp.status_code == 404
    assert _busca_clave(resp.json(), "advertencia_producto_inexistente")
    assert _contar_filas(db_session) == {
        "ordenes": 0,
        "piezas": 0,
        "recortes": 0,
        "productos": 0,
    }


def test_crear_orden_confirma_creacion_automatica_y_alerta_stock_bajo_201(
    client, auth_headers, db_session
):
    resp = client.post(
        "/api/ordenes",
        headers=auth_headers,
        json=_orden_payload(
            material="INOX",
            largo_mm=999.0,
            ancho_mm=999.0,
            multiplicidad=3,
            confirmar_creacion_automatica=True,
        ),
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["producto_comprometido"]["creado_automaticamente"] is True
    assert body["alerta_stock_bajo"] is True

    from app.models.producto import Producto

    producto = db_session.get(Producto, body["producto_comprometido"]["id"])
    assert producto is not None
    assert producto.material == "INOX"
    assert producto.stock_fisico == 0.0
    assert producto.stock_comprometido == 3.0
    assert _contar_filas(db_session) == {
        "ordenes": 1,
        "piezas": 1,
        "recortes": 1,
        "productos": 1,
    }


def test_crear_orden_rollback_total_si_falla_creacion_automatica_500(
    client, auth_headers, db_session, monkeypatch
):
    from sqlalchemy.orm import Session

    def flush_que_falla(self, *args, **kwargs):
        self.rollback()
        raise RuntimeError("fallo simulado en la transacción")

    monkeypatch.setattr(Session, "flush", flush_que_falla)

    resp = client.post(
        "/api/ordenes",
        headers=auth_headers,
        json=_orden_payload(
            material="INOX",
            largo_mm=999.0,
            ancho_mm=999.0,
            confirmar_creacion_automatica=True,
        ),
    )
    assert resp.status_code == 500

    monkeypatch.undo()
    assert _contar_filas(db_session) == {
        "ordenes": 0,
        "piezas": 0,
        "recortes": 0,
        "productos": 0,
    }


def test_crear_orden_recorte_con_dimensiones_incompletas_422(client, auth_headers, db_session):
    _crear_producto(db_session)
    resp = client.post(
        "/api/ordenes",
        headers=auth_headers,
        json=_orden_payload(recortes=[{"largo_mm": None, "ancho_mm": None}]),
    )
    assert resp.status_code == 422
    assert _contar_filas(db_session) == {
        "ordenes": 0,
        "piezas": 0,
        "recortes": 0,
        "productos": 1,
    }


def test_crear_orden_requiere_autenticacion_401(client):
    resp = client.post("/api/ordenes", json=_orden_payload())
    assert resp.status_code == 401
