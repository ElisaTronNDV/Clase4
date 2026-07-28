def test_ruta_protegida_sin_token_401(client):
    resp = client.get("/api/ordenes")
    assert resp.status_code == 401


def test_ruta_protegida_con_token_valido_acceso_concedido(client, auth_headers):
    resp = client.get("/api/ordenes", headers=auth_headers)
    assert resp.status_code == 200


def test_usuario_autenticado_accede_a_todos_los_modulos_sin_restriccion_de_rol(
    client, auth_headers
):
    assert client.get("/api/ordenes", headers=auth_headers).status_code == 200
    assert client.get("/api/productos", headers=auth_headers).status_code == 200
    assert client.get("/api/configuracion", headers=auth_headers).status_code == 200


def test_token_invalido_401(client):
    resp = client.get("/api/ordenes", headers={"Authorization": "Bearer token-invalido"})
    assert resp.status_code == 401
