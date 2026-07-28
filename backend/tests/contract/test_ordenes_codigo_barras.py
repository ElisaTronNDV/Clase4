import io

from PIL import Image
from pyzbar.pyzbar import decode as decode_barcode


def _crear_orden(db_session, codigo_nest="NEST-000001", estado="vigente"):
    from app.models.orden_trabajo import OrdenTrabajo

    orden = OrdenTrabajo(
        codigo_nest=codigo_nest,
        estado=estado,
        multiplicidad=1,
        espesor_mm=2.1,
        material="SAE_1010",
        largo_mm=1200.0,
        ancho_mm=600.0,
        tiempo_ejecucion_estimado="00:01:22",
    )
    db_session.add(orden)
    db_session.commit()
    db_session.refresh(orden)
    return orden


def test_codigo_barras_devuelve_png_decodificable_200(client, auth_headers, db_session):
    orden = _crear_orden(db_session, codigo_nest="NEST-000042")

    resp = client.get(f"/api/ordenes/{orden.id}/codigo-barras", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"

    imagen = Image.open(io.BytesIO(resp.content))
    resultados = decode_barcode(imagen)
    assert len(resultados) == 1
    assert resultados[0].data.decode() == "NEST-000042"
    assert resultados[0].type == "CODE128"


def test_codigo_barras_orden_inexistente_404(client, auth_headers):
    resp = client.get("/api/ordenes/999999/codigo-barras", headers=auth_headers)
    assert resp.status_code == 404


def test_codigo_barras_requiere_autenticacion_401(client, db_session):
    orden = _crear_orden(db_session)

    resp = client.get(f"/api/ordenes/{orden.id}/codigo-barras")
    assert resp.status_code == 401
