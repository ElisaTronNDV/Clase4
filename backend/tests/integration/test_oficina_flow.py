import io
import re
from pathlib import Path

from PIL import Image
from pyzbar.pyzbar import decode as decode_barcode

FIXTURES_DIR = Path(__file__).resolve().parents[3] / "Archivos de Corte"
CODIGO_NEST_RE = re.compile(r"^NEST-\d{6}$")


def _pdf_bytes(nombre: str) -> bytes:
    return (FIXTURES_DIR / nombre).read_bytes()


def _crear_producto_coincidente(db_session, **overrides):
    from app.models.producto import Producto

    datos = dict(
        material="SAE_1010",
        espesor_mm=8.0,
        largo_mm=3000.0,
        ancho_mm=1500.0,
        stock_fisico=20.0,
        stock_comprometido=0.0,
        punto_pedido=2.0,
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
    from app.models.recorte_declarado import RecorteDeclarado

    return {
        "ordenes": db_session.query(OrdenTrabajo).count(),
        "piezas": db_session.query(Pieza).count(),
        "recortes": db_session.query(RecorteDeclarado).count(),
    }


def test_flujo_completo_subir_pdf_editar_confirmar_nest_y_stock(client, auth_headers, db_session):
    producto = _crear_producto_coincidente(db_session, stock_fisico=20.0, punto_pedido=2.0)

    # 1. Subir el PDF y obtener la propuesta editable, sin persistir nada (Principios II/III).
    resp_extraer = client.post(
        "/api/ordenes/extraer-pdf",
        headers=auth_headers,
        files={"archivo": ("Ejemplo 3.pdf", _pdf_bytes("Ejemplo 3.pdf"), "application/pdf")},
    )
    assert resp_extraer.status_code == 200
    propuestas = resp_extraer.json()
    assert len(propuestas) == 1
    propuesta = propuestas[0]
    assert propuesta["extraccion_incompleta"] is False
    assert propuesta["material"] == "SAE_1010"
    assert len(propuesta["piezas"]) == 2
    assert len(propuesta["recortes"]) == 2
    assert _contar_filas(db_session) == {"ordenes": 0, "piezas": 0, "recortes": 0}

    # 2. El usuario revisa y edita la propuesta antes de confirmar (multiplicidad y una pieza).
    propuesta["multiplicidad"] = 4
    propuesta["piezas"][0]["cantidad"] = 10

    # 3. Confirmar la orden.
    resp_crear = client.post("/api/ordenes", headers=auth_headers, json=propuesta)
    assert resp_crear.status_code == 201
    orden = resp_crear.json()
    assert CODIGO_NEST_RE.match(orden["codigo_nest"])
    assert orden["estado"] == "vigente"
    assert orden["producto_comprometido"]["id"] == producto.id
    assert orden["producto_comprometido"]["creado_automaticamente"] is False
    assert orden["alerta_stock_bajo"] is False

    # 4. El compromiso de stock es igual a la multiplicidad editada (FR-014).
    db_session.refresh(producto)
    assert producto.stock_comprometido == 4.0
    assert producto.stock_fisico == 20.0

    # 5. Las filas quedan persistidas recién ahora, con los datos editados (FR-010/FR-011).
    assert _contar_filas(db_session) == {"ordenes": 1, "piezas": 2, "recortes": 2}

    from app.models.pieza import Pieza

    pieza_editada = (
        db_session.query(Pieza).filter_by(orden_id=orden["id"]).order_by(Pieza.id).first()
    )
    assert pieza_editada.cantidad == 10

    # 6. La orden aparece en el listado como vigente y buscable por NEST.
    resp_listado = client.get(
        "/api/ordenes", headers=auth_headers, params={"estado": "vigente"}
    )
    assert resp_listado.status_code == 200
    assert orden["codigo_nest"] in {o["codigo_nest"] for o in resp_listado.json()}

    # 7. El código de barras del NEST impreso decodifica correctamente (FR-013, RNF-06).
    resp_barras = client.get(
        f"/api/ordenes/{orden['id']}/codigo-barras", headers=auth_headers
    )
    assert resp_barras.status_code == 200
    assert resp_barras.headers["content-type"] == "image/png"
    imagen = Image.open(io.BytesIO(resp_barras.content))
    resultados = decode_barcode(imagen)
    assert len(resultados) == 1
    assert resultados[0].data.decode() == orden["codigo_nest"]
