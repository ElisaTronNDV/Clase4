import io
import re

import pdfplumber

_PATRON_DIMENSIONES_RECORTE = re.compile(r"^(\d+(?:[.,]\d+)?)\s*[xX]\s*(\d+(?:[.,]\d+)?)")
_ENCABEZADO_PIEZAS = "Ref. Cant. Pieza Descripción"
_DESCRIPCION_RECORTE = "Saved scrap"
_PATRON_PIEZA = re.compile(r"^(\d+)\s+(\d+)\s+(\S+)\s+(.+)$")


def parsear_dimensiones_recorte(nombre_tecnico: str) -> tuple[float | None, float | None]:
    """Extrae largo/ancho del nombre técnico de un recorte (ej. "800x400" o
    "1085.00x1500.00_RECT_SCRAP"). Devuelve (None, None) si no matchea (research.md §2)."""
    coincidencia = _PATRON_DIMENSIONES_RECORTE.match(nombre_tecnico.strip())
    if not coincidencia:
        return None, None
    largo = float(coincidencia.group(1).replace(",", "."))
    ancho = float(coincidencia.group(2).replace(",", "."))
    return largo, ancho


def _campo(texto: str, etiqueta: str, patron_valor: str) -> str | None:
    coincidencia = re.search(re.escape(etiqueta) + r"\s+" + patron_valor, texto)
    return coincidencia.group(1).strip() if coincidencia else None


def _extraer_piezas_y_recortes(texto: str) -> tuple[list[dict], list[dict], bool]:
    lineas = texto.splitlines()
    try:
        inicio = lineas.index(_ENCABEZADO_PIEZAS) + 1
    except ValueError:
        return [], [], True

    piezas: list[dict] = []
    recortes: list[dict] = []
    for linea in lineas[inicio:]:
        if linea.startswith("salvagnini"):
            break
        if linea.endswith(_DESCRIPCION_RECORTE):
            resto = linea[: -len(_DESCRIPCION_RECORTE)].strip()
            nombre_tecnico = resto.split(None, 1)[-1] if resto else ""
            largo, ancho = parsear_dimensiones_recorte(nombre_tecnico)
            recortes.append({"largo_mm": largo, "ancho_mm": ancho})
            continue
        coincidencia = _PATRON_PIEZA.match(linea)
        if coincidencia:
            piezas.append(
                {"descripcion": coincidencia.group(4), "cantidad": int(coincidencia.group(2))}
            )
    return piezas, recortes, False


def extraer_propuesta(pdf_bytes: bytes) -> dict:
    """Extrae una propuesta editable del archivo de corte (FR-008, FR-009). Nunca lanza
    por estructura inesperada: campos no encontrados quedan en None y
    extraccion_incompleta pasa a True (edge case del spec, nunca bloquea la carga)."""
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        texto = pdf.pages[0].extract_text() or ""

    multiplicidad = _campo(texto, "Multiplicidad", r"(\d+)")
    espesor = _campo(texto, "Espesor [mm]", r"([\d.,]+)")
    material = _campo(texto, "Material", r"(\S+)")
    tiempo = _campo(texto, "Tiempo de ejecución estimado", r"([\d:]+)")

    largo = ancho = None
    coincidencia_dims = re.search(r"Dimensiones \[mm\]\s+([\d.,]+)\s*x\s*([\d.,]+)", texto)
    if coincidencia_dims:
        largo = float(coincidencia_dims.group(1).replace(",", "."))
        ancho = float(coincidencia_dims.group(2).replace(",", "."))

    piezas, recortes, encabezado_faltante = _extraer_piezas_y_recortes(texto)

    campos_generales = (multiplicidad, espesor, material, tiempo, largo, ancho)
    extraccion_incompleta = encabezado_faltante or any(
        campo is None for campo in campos_generales
    )

    return {
        "multiplicidad": int(multiplicidad) if multiplicidad else None,
        "espesor_mm": float(espesor.replace(",", ".")) if espesor else None,
        "material": material,
        "largo_mm": largo,
        "ancho_mm": ancho,
        "tiempo_ejecucion_estimado": tiempo,
        "piezas": piezas,
        "recortes": recortes,
        "extraccion_incompleta": extraccion_incompleta,
    }
