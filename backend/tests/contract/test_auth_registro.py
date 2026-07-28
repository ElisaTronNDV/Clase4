def test_registro_exitoso(client):
    resp = client.post(
        "/api/auth/registro", json={"email": "nuevo@dyp.com", "password": "password123"}
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "nuevo@dyp.com"
    assert "id" in body
    assert "password" not in body
    assert "password_hash" not in body


def test_registro_email_duplicado_409(client):
    client.post("/api/auth/registro", json={"email": "dup@dyp.com", "password": "password123"})
    resp = client.post(
        "/api/auth/registro", json={"email": "dup@dyp.com", "password": "otrapassword"}
    )
    assert resp.status_code == 409


def test_registro_password_corta_422(client):
    resp = client.post(
        "/api/auth/registro", json={"email": "corta@dyp.com", "password": "1234567"}
    )
    assert resp.status_code == 422


def test_registro_password_sin_requisito_de_composicion(client):
    resp = client.post(
        "/api/auth/registro", json={"email": "simple@dyp.com", "password": "sololetras"}
    )
    assert resp.status_code == 201
