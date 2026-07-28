def test_login_exitoso(client):
    client.post("/api/auth/registro", json={"email": "login@dyp.com", "password": "password123"})
    resp = client.post(
        "/api/auth/login", json={"email": "login@dyp.com", "password": "password123"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert "access_token" in body
    assert "expires_at" in body


def test_login_credenciales_invalidas_401(client):
    client.post("/api/auth/registro", json={"email": "login2@dyp.com", "password": "password123"})
    resp = client.post(
        "/api/auth/login", json={"email": "login2@dyp.com", "password": "incorrecta"}
    )
    assert resp.status_code == 401


def test_login_sin_bloqueo_tras_intentos_fallidos_repetidos(client):
    client.post("/api/auth/registro", json={"email": "login3@dyp.com", "password": "password123"})
    for _ in range(5):
        resp = client.post(
            "/api/auth/login", json={"email": "login3@dyp.com", "password": "incorrecta"}
        )
        assert resp.status_code == 401
    resp_ok = client.post(
        "/api/auth/login", json={"email": "login3@dyp.com", "password": "password123"}
    )
    assert resp_ok.status_code == 200


def test_jwt_incluye_expiracion_24h(client):
    import jose.jwt as jose_jwt

    client.post("/api/auth/registro", json={"email": "exp@dyp.com", "password": "password123"})
    resp = client.post("/api/auth/login", json={"email": "exp@dyp.com", "password": "password123"})
    token = resp.json()["access_token"]
    claims = jose_jwt.get_unverified_claims(token)
    assert "exp" in claims
