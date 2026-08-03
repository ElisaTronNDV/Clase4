import io
from pathlib import Path

import pytest
from PIL import Image

FIXTURES_DIR = Path(__file__).resolve().parents[3] / "Archivos de Corte"


def _pdf_bytes(nombre: str) -> bytes:
    return (FIXTURES_DIR / nombre).read_bytes()


def _pdf_en_blanco() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (200, 200), color="white").save(buf, format="PDF")
    return buf.getvalue()


def test_extraer_propuesta_tablas_completas_sin_recortes():
    from app.services.pdf_extraction import extraer_propuesta

    propuestas = extraer_propuesta(_pdf_bytes("Ejemplo 1.pdf"))

    assert len(propuestas) == 1
    propuesta = propuestas[0]
    assert propuesta["extraccion_incompleta"] is False
    assert propuesta["multiplicidad"] == 1
    assert propuesta["espesor_mm"] == pytest.approx(12.7)
    assert propuesta["material"] == "SAE_1010"
    assert propuesta["largo_mm"] == pytest.approx(1310.0)
    assert propuesta["ancho_mm"] == pytest.approx(580.0)
    assert propuesta["tiempo_ejecucion_estimado"] == "00:26:19"
    assert propuesta["piezas"] == [
        {"descripcion": "PC 1368 (CO) X3", "cantidad": 3},
        {"descripcion": "PC 1368 (CO) X3", "cantidad": 3},
        {"descripcion": "PC 1368 (CO) X6", "cantidad": 6},
        {"descripcion": "PC 1362 (CO) X3", "cantidad": 3},
    ]
    assert propuesta["recortes"] == []


def test_extraer_propuesta_tablas_completas_con_recortes():
    from app.services.pdf_extraction import extraer_propuesta

    propuestas = extraer_propuesta(_pdf_bytes("Ejemplo 3.pdf"))

    assert len(propuestas) == 1
    propuesta = propuestas[0]
    assert propuesta["extraccion_incompleta"] is False
    assert propuesta["multiplicidad"] == 1
    assert propuesta["espesor_mm"] == pytest.approx(8.0)
    assert propuesta["material"] == "SAE_1010"
    assert propuesta["largo_mm"] == pytest.approx(3000.0)
    assert propuesta["ancho_mm"] == pytest.approx(1500.0)
    assert propuesta["tiempo_ejecucion_estimado"] == "00:26:51"
    assert propuesta["piezas"] == [
        {"descripcion": "PC 1388 X1/ PC 1363 X1/ PC 1362 X5 (C/P) BOUNOUS", "cantidad": 7},
        {"descripcion": "PC 1363 X24 (CO) BOUNOUS", "cantidad": 24},
    ]
    assert propuesta["recortes"] == [
        {"largo_mm": pytest.approx(1085.0), "ancho_mm": pytest.approx(1500.0)},
        {"largo_mm": pytest.approx(955.0), "ancho_mm": pytest.approx(559.16)},
    ]


def test_extraer_propuesta_pdf_con_varias_paginas_devuelve_una_propuesta_por_pagina():
    from app.services.pdf_extraction import extraer_propuesta

    propuestas = extraer_propuesta(_pdf_bytes("Ejemplo 2.pdf"))

    assert len(propuestas) == 3
    assert [p["tiempo_ejecucion_estimado"] for p in propuestas] == [
        "00:01:44",
        "00:02:29",
        "00:02:13",
    ]
    assert [len(p["piezas"]) for p in propuestas] == [6, 5, 5]
    for propuesta in propuestas:
        assert propuesta["extraccion_incompleta"] is False
        assert propuesta["multiplicidad"] == 1
        assert propuesta["espesor_mm"] == pytest.approx(0.91)
        assert propuesta["material"] == "SAE_1010"
        assert propuesta["largo_mm"] == pytest.approx(3000.0)
        assert propuesta["ancho_mm"] == pytest.approx(1500.0)
        assert propuesta["recortes"] == []


def test_extraer_propuesta_tabla_faltante_no_bloquea():
    from app.services.pdf_extraction import extraer_propuesta

    propuestas = extraer_propuesta(_pdf_en_blanco())

    assert len(propuestas) == 1
    propuesta = propuestas[0]
    assert propuesta["extraccion_incompleta"] is True
    assert propuesta["multiplicidad"] is None
    assert propuesta["espesor_mm"] is None
    assert propuesta["material"] is None
    assert propuesta["largo_mm"] is None
    assert propuesta["ancho_mm"] is None
    assert propuesta["tiempo_ejecucion_estimado"] is None
    assert propuesta["piezas"] == []
    assert propuesta["recortes"] == []


@pytest.mark.parametrize(
    "nombre_tecnico,largo_esperado,ancho_esperado",
    [
        ("800x400", 800.0, 400.0),
        ("800X400", 800.0, 400.0),
        ("800,5x400,25", 800.5, 400.25),
        ("800.5X400.25", 800.5, 400.25),
        ("1085.00x1500.00_RECT_SCRAP", 1085.0, 1500.0),
        ("955.00x559.16_RECT_SCRAP", 955.0, 559.16),
        ("  800x400  ", 800.0, 400.0),
    ],
)
def test_parsear_dimensiones_recorte_variantes_validas(
    nombre_tecnico, largo_esperado, ancho_esperado
):
    from app.services.pdf_extraction import parsear_dimensiones_recorte

    largo, ancho = parsear_dimensiones_recorte(nombre_tecnico)
    assert largo == pytest.approx(largo_esperado)
    assert ancho == pytest.approx(ancho_esperado)


@pytest.mark.parametrize("nombre_tecnico", ["", "SCRAP_SIN_DIMENSIONES", "x400", "800x"])
def test_parsear_dimensiones_recorte_no_matchea_devuelve_none(nombre_tecnico):
    from app.services.pdf_extraction import parsear_dimensiones_recorte

    largo, ancho = parsear_dimensiones_recorte(nombre_tecnico)
    assert largo is None
    assert ancho is None
