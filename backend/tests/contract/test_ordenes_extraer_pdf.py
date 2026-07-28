from pathlib import Path

FIXTURES_DIR = Path(__file__).resolve().parents[3] / "Archivos de Corte"


def _pdf_bytes(nombre: str) -> bytes:
    return (FIXTURES_DIR / nombre).read_bytes()


def _sin_filas_persistidas(db_session) -> bool:
    from app.models.orden_trabajo import OrdenTrabajo
    from app.models.pieza import Pieza
    from app.models.recorte_declarado import RecorteDeclarado

    return (
        db_session.query(OrdenTrabajo).count() == 0
        and db_session.query(Pieza).count() == 0
        and db_session.query(RecorteDeclarado).count() == 0
    )


def test_extraer_pdf_completo_200(client, auth_headers, db_session):
    archivo = _pdf_bytes("Ejemplo 3.pdf")
    resp = client.post(
        "/api/ordenes/extraer-pdf",
        headers=auth_headers,
        files={"archivo": ("Ejemplo 3.pdf", archivo, "application/pdf")},
    )
    assert resp.status_code == 200
    body = resp.json()
    for campo in (
        "multiplicidad",
        "espesor_mm",
        "material",
        "largo_mm",
        "ancho_mm",
        "tiempo_ejecucion_estimado",
        "piezas",
        "recortes",
        "extraccion_incompleta",
    ):
        assert campo in body
    assert body["material"] == "SAE_1010"
    assert body["multiplicidad"] == 1
    assert body["extraccion_incompleta"] is False
    assert len(body["piezas"]) >= 1
    assert len(body["recortes"]) == 2
    assert _sin_filas_persistidas(db_session)


def test_extraer_pdf_con_recortes_parsea_dimensiones(client, auth_headers, db_session):
    archivo = _pdf_bytes("Ejemplo 3.pdf")
    resp = client.post(
        "/api/ordenes/extraer-pdf",
        headers=auth_headers,
        files={"archivo": ("Ejemplo 3.pdf", archivo, "application/pdf")},
    )
    assert resp.status_code == 200
    recortes = resp.json()["recortes"]
    dimensiones = {(r["largo_mm"], r["ancho_mm"]) for r in recortes}
    assert (1085.0, 1500.0) in dimensiones
    assert (955.0, 559.16) in dimensiones
    assert _sin_filas_persistidas(db_session)


def test_extraer_pdf_no_es_pdf_400(client, auth_headers, db_session):
    resp = client.post(
        "/api/ordenes/extraer-pdf",
        headers=auth_headers,
        files={"archivo": ("archivo.txt", b"esto no es un pdf", "text/plain")},
    )
    assert resp.status_code == 400
    assert _sin_filas_persistidas(db_session)


def test_extraer_pdf_mayor_a_20mb_413(client, auth_headers, db_session):
    archivo_grande = b"%PDF-1.4\n" + b"0" * (20 * 1024 * 1024 + 1)
    resp = client.post(
        "/api/ordenes/extraer-pdf",
        headers=auth_headers,
        files={"archivo": ("grande.pdf", archivo_grande, "application/pdf")},
    )
    assert resp.status_code == 413
    assert _sin_filas_persistidas(db_session)


def test_extraer_pdf_tabla_faltante_extraccion_incompleta(client, auth_headers, db_session):
    from io import BytesIO

    from PIL import Image

    imagen_en_blanco = BytesIO()
    Image.new("RGB", (200, 200), color="white").save(imagen_en_blanco, format="PDF")

    resp = client.post(
        "/api/ordenes/extraer-pdf",
        headers=auth_headers,
        files={"archivo": ("sin_tablas.pdf", imagen_en_blanco.getvalue(), "application/pdf")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["extraccion_incompleta"] is True
    assert body["piezas"] == []
    assert body["recortes"] == []
    assert _sin_filas_persistidas(db_session)


def test_extraer_pdf_requiere_autenticacion_401(client):
    archivo = _pdf_bytes("Ejemplo 1.pdf")
    resp = client.post(
        "/api/ordenes/extraer-pdf",
        files={"archivo": ("Ejemplo 1.pdf", archivo, "application/pdf")},
    )
    assert resp.status_code == 401
