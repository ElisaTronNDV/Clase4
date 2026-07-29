import io

import barcode
from barcode.writer import ImageWriter
from PIL import Image
from pyzbar.pyzbar import decode as decode_barcode

MODULE_WIDTH_MM = 0.4  # >= 0.33mm mínimo legible a resolución de impresión (RNF-06)


class GeneracionCodigoBarrasError(Exception):
    """La imagen generada no decodificó de forma independiente antes de servirse."""


def generar_codigo_barras_png(valor: str) -> bytes:
    """Genera el PNG del código de barras CODE_128 del NEST y lo verifica decodificándolo
    con pyzbar antes de devolverlo — nunca se da por buena una imagen solo porque se
    generó, tiene que decodificar como lo haría un lector estándar (research.md §5,
    FR-013, RNF-06)."""
    codigo = barcode.get("code128", valor, writer=ImageWriter())
    buffer = io.BytesIO()
    codigo.write(buffer, options={"module_width": MODULE_WIDTH_MM, "write_text": False})
    datos_png = buffer.getvalue()

    imagen = Image.open(io.BytesIO(datos_png))
    resultados = decode_barcode(imagen)
    if len(resultados) != 1 or resultados[0].data.decode() != valor:
        raise GeneracionCodigoBarrasError(
            f"El código de barras generado para {valor!r} no decodificó correctamente"
        )

    return datos_png
