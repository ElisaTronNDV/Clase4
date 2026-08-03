"""SC-001 (accuracy por campo), SC-002 (latencia de extracción) y SC-003 (latencia de
listados/búsquedas), medidos contra la muestra de PDFs reales de `Archivos de Corte/`
(Clarifications 2026-07-22: SC-001 se mide por campo individual, no por documento completo).

El ground truth de cada PDF se estableció leyendo manualmente su contenido crudo (texto y tablas
de pdfplumber) — no se infiere del propio extractor bajo prueba.
"""

import time
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).resolve().parents[3] / "Archivos de Corte"

GROUND_TRUTH = {
    "Ejemplo 1.pdf": {
        "generales": {
            "multiplicidad": 1,
            "espesor_mm": 12.7,
            "material": "SAE_1010",
            "largo_mm": 1310.0,
            "ancho_mm": 580.0,
            "tiempo_ejecucion_estimado": "00:26:19",
        },
        "piezas": [
            {"descripcion": "PC 1368 (CO) X3", "cantidad": 3},
            {"descripcion": "PC 1368 (CO) X3", "cantidad": 3},
            {"descripcion": "PC 1368 (CO) X6", "cantidad": 6},
            {"descripcion": "PC 1362 (CO) X3", "cantidad": 3},
        ],
        "recortes": [],
    },
    "Ejemplo 2.pdf": {
        # Ground truth de la página 1/3 del nest (primer formato); el extractor devuelve
        # una propuesta por página, acá solo se mide accuracy sobre la primera.
        "generales": {
            "multiplicidad": 1,
            "espesor_mm": 0.91,
            "material": "SAE_1010",
            "largo_mm": 3000.0,
            "ancho_mm": 1500.0,
            "tiempo_ejecucion_estimado": "00:01:44",
        },
        "piezas": [
            {"descripcion": "PC X1 (C/P) PPTO4200", "cantidad": 1},
            {"descripcion": "PC X2 (C/PAN) PPTO4200", "cantidad": 2},
            {"descripcion": "PC X2 (C/PAN) PPTO4200", "cantidad": 2},
            {"descripcion": "PC X1 (C/PAN) PPTO 4201", "cantidad": 1},
            {"descripcion": "PC X2 (C/PAN) PPTO4200", "cantidad": 2},
            {"descripcion": "PC X2 (C/PAN) PPTO 4201", "cantidad": 1},
        ],
        "recortes": [],
    },
    "Ejemplo 3.pdf": {
        "generales": {
            "multiplicidad": 1,
            "espesor_mm": 8.0,
            "material": "SAE_1010",
            "largo_mm": 3000.0,
            "ancho_mm": 1500.0,
            "tiempo_ejecucion_estimado": "00:26:51",
        },
        "piezas": [
            {"descripcion": "PC 1388 X1/ PC 1363 X1/ PC 1362 X5 (C/P) BOUNOUS", "cantidad": 7},
            {"descripcion": "PC 1363 X24 (CO) BOUNOUS", "cantidad": 24},
        ],
        "recortes": [
            {"largo_mm": 1085.0, "ancho_mm": 1500.0},
            {"largo_mm": 955.0, "ancho_mm": 559.16},
        ],
    },
}

TOLERANCIA_NUMERICA = 0.01


def _campos_coinciden(esperado, obtenido) -> bool:
    if isinstance(esperado, float):
        return obtenido is not None and abs(obtenido - esperado) <= TOLERANCIA_NUMERICA
    return obtenido == esperado


def _contar_campos(ground_truth: dict, propuesta: dict) -> tuple[int, int]:
    """Devuelve (campos_correctos, campos_totales) comparando cada campo individual."""
    correctos = 0
    total = 0

    for campo, esperado in ground_truth["generales"].items():
        total += 1
        if _campos_coinciden(esperado, propuesta.get(campo)):
            correctos += 1

    piezas_obtenidas = propuesta.get("piezas") or []
    for i, pieza_esperada in enumerate(ground_truth["piezas"]):
        pieza_obtenida = piezas_obtenidas[i] if i < len(piezas_obtenidas) else {}
        for campo, esperado in pieza_esperada.items():
            total += 1
            if _campos_coinciden(esperado, pieza_obtenida.get(campo)):
                correctos += 1

    recortes_obtenidos = propuesta.get("recortes") or []
    for i, recorte_esperado in enumerate(ground_truth["recortes"]):
        recorte_obtenido = recortes_obtenidos[i] if i < len(recortes_obtenidos) else {}
        for campo, esperado in recorte_esperado.items():
            total += 1
            if _campos_coinciden(esperado, recorte_obtenido.get(campo)):
                correctos += 1

    return correctos, total


def test_sc001_accuracy_extraccion_por_campo_individual_al_menos_98_por_ciento():
    from app.services.pdf_extraction import extraer_propuesta

    correctos_total = 0
    campos_total = 0

    for nombre, ground_truth in GROUND_TRUTH.items():
        contenido = (FIXTURES_DIR / nombre).read_bytes()
        propuesta = extraer_propuesta(contenido)[0]
        correctos, total = _contar_campos(ground_truth, propuesta)
        accuracy_doc = correctos / total
        print(f"{nombre}: {correctos}/{total} campos correctos ({accuracy_doc:.1%})")
        correctos_total += correctos
        campos_total += total

    accuracy = correctos_total / campos_total
    print(f"TOTAL: {correctos_total}/{campos_total} campos correctos ({accuracy:.1%})")
    assert accuracy >= 0.98, (
        f"SC-001: accuracy de extracción por campo {accuracy:.1%} por debajo del 98% requerido"
    )


@pytest.mark.parametrize("nombre_pdf", list(GROUND_TRUTH.keys()))
def test_sc002_latencia_extraccion_pdf_bajo_10s(nombre_pdf):
    from app.services.pdf_extraction import extraer_propuesta

    contenido = (FIXTURES_DIR / nombre_pdf).read_bytes()

    inicio = time.perf_counter()
    extraer_propuesta(contenido)
    elapsed = time.perf_counter() - inicio

    print(f"{nombre_pdf}: extracción en {elapsed:.3f}s")
    assert elapsed < 10.0, f"SC-002: extracción de {nombre_pdf} tardó {elapsed:.3f}s (>= 10s)"


def _crear_ordenes_y_productos(db_session, cantidad: int):
    from app.models.orden_trabajo import OrdenTrabajo
    from app.models.producto import Producto

    for i in range(cantidad):
        db_session.add(
            Producto(
                material="SAE_1010",
                espesor_mm=2.0,
                largo_mm=1000.0 + i,
                ancho_mm=500.0,
                stock_fisico=10.0,
                stock_comprometido=0.0,
                punto_pedido=2.0,
            )
        )
        db_session.add(
            OrdenTrabajo(
                codigo_nest=f"NEST-{i:06d}",
                estado="vigente" if i % 2 == 0 else "cerrada",
                multiplicidad=1,
                espesor_mm=2.0,
                material="SAE_1010",
                largo_mm=1000.0 + i,
                ancho_mm=500.0,
                tiempo_ejecucion_estimado="00:01:00",
            )
        )
    db_session.commit()


def _percentil_95(valores: list[float]) -> float:
    valores_ordenados = sorted(valores)
    indice = max(0, int(round(0.95 * (len(valores_ordenados) - 1))))
    return valores_ordenados[indice]


def test_sc003_latencia_listados_p95_bajo_2s(client, auth_headers, db_session):
    _crear_ordenes_y_productos(db_session, cantidad=200)

    tiempos_ordenes = []
    tiempos_productos = []
    repeticiones = 20

    for _ in range(repeticiones):
        inicio = time.perf_counter()
        resp = client.get("/api/ordenes", headers=auth_headers)
        tiempos_ordenes.append(time.perf_counter() - inicio)
        assert resp.status_code == 200

        inicio = time.perf_counter()
        resp = client.get("/api/productos", headers=auth_headers)
        tiempos_productos.append(time.perf_counter() - inicio)
        assert resp.status_code == 200

    p95_ordenes = _percentil_95(tiempos_ordenes)
    p95_productos = _percentil_95(tiempos_productos)
    print(f"GET /api/ordenes p95={p95_ordenes:.3f}s sobre {repeticiones} llamadas (200 filas)")
    print(f"GET /api/productos p95={p95_productos:.3f}s sobre {repeticiones} llamadas (200 filas)")

    assert p95_ordenes < 2.0, f"SC-003: p95 de GET /api/ordenes {p95_ordenes:.3f}s (>= 2s)"
    assert p95_productos < 2.0, f"SC-003: p95 de GET /api/productos {p95_productos:.3f}s (>= 2s)"
