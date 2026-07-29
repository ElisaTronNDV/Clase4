def test_actualizar_configuracion_200(client, auth_headers, db_session):
    resp = client.put(
        "/api/configuracion", headers=auth_headers, json={"margen_tolerancia_mm": 1.5}
    )
    assert resp.status_code == 200
    assert resp.json() == {"margen_tolerancia_mm": 1.5}

    resp_get = client.get("/api/configuracion", headers=auth_headers)
    assert resp_get.json() == {"margen_tolerancia_mm": 1.5}


def test_actualizar_configuracion_valor_cero_422(client, auth_headers, db_session):
    resp = client.put(
        "/api/configuracion", headers=auth_headers, json={"margen_tolerancia_mm": 0}
    )
    assert resp.status_code == 422


def test_actualizar_configuracion_valor_negativo_422(client, auth_headers, db_session):
    resp = client.put(
        "/api/configuracion", headers=auth_headers, json={"margen_tolerancia_mm": -1.0}
    )
    assert resp.status_code == 422


def test_actualizar_configuracion_sin_limite_superior(client, auth_headers, db_session):
    resp = client.put(
        "/api/configuracion", headers=auth_headers, json={"margen_tolerancia_mm": 1000.0}
    )
    assert resp.status_code == 200
    assert resp.json() == {"margen_tolerancia_mm": 1000.0}


def test_actualizar_configuracion_cambia_resultado_de_matching(
    client, auth_headers, db_session
):
    from app.models.producto import Producto

    producto = Producto(
        material="SAE_1010",
        espesor_mm=2.1,
        largo_mm=1200.0,
        ancho_mm=600.0,
        stock_fisico=10.0,
        stock_comprometido=0.0,
        punto_pedido=3.0,
    )
    db_session.add(producto)
    db_session.commit()

    client.put("/api/configuracion", headers=auth_headers, json={"margen_tolerancia_mm": 0.1})

    payload = {
        "multiplicidad": 1,
        "espesor_mm": 2.1,
        "material": "SAE_1010",
        "largo_mm": 1205.0,
        "ancho_mm": 600.0,
        "tiempo_ejecucion_estimado": "00:01:00",
        "piezas": [],
        "recortes": [],
    }
    resp_sin_match = client.post("/api/ordenes", headers=auth_headers, json=payload)
    assert resp_sin_match.status_code == 404

    client.put("/api/configuracion", headers=auth_headers, json={"margen_tolerancia_mm": 10.0})
    resp_con_match = client.post("/api/ordenes", headers=auth_headers, json=payload)
    assert resp_con_match.status_code == 201
    assert resp_con_match.json()["producto_comprometido"]["id"] == producto.id


def test_actualizar_configuracion_requiere_autenticacion_401(client):
    resp = client.put("/api/configuracion", json={"margen_tolerancia_mm": 1.5})
    assert resp.status_code == 401
