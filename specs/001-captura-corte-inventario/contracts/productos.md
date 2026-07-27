# Contract: Maestro de Productos (Historia 4)

Todas las rutas requieren autenticación. Cubre FR-024 a FR-028.

## POST /api/productos

Alta manual de un producto (FR-024, FR-025, FR-026).

**Request**:
```json
{
  "material": "SAE_1010",
  "espesor_mm": 2.1,
  "largo_mm": 1200,
  "ancho_mm": 600,
  "stock_fisico": 10,
  "punto_pedido": 3
}
```

**Response 201**: `{ "id": 15, ...mismo shape... , "stock_comprometido": 0 }`

**Response 422**: falta algún campo obligatorio (FR-024) — el detalle señala los campos faltantes.

**Response 409**: ya existe un producto con `material`, `espesor_mm`, `largo_mm`, `ancho_mm`
exactamente iguales (FR-026; comparación exacta, no de tolerancia).

## GET /api/productos

Listado completo del maestro (FR-028).

**Response 200**: `[{ "id": 1, "material": "...", ..., "stock_comprometido": 0,
"alerta_stock_bajo": false }, ...]`

`alerta_stock_bajo` es `stock_fisico - stock_comprometido <= punto_pedido` (FR-016); el frontend
MUST mostrar un badge/ícono junto al stock quando este flag es `true`, únicamente en este listado
de Inventario (ver Clarifications 2026-07-22 en `spec.md`) — no en el listado/confirmación de
órdenes.

## PUT /api/productos/{id}

Edición de un producto existente (FR-027).

**Request**: mismo shape que el alta, sin `stock_comprometido` (campo no aceptado en este
endpoint — si viene en el body, se ignora o se rechaza con 422, a decidir en implementación, pero
en ningún caso se aplica).

**Response 200**: producto actualizado.

**Response 409**: la edición de `material`/`espesor_mm`/`largo_mm`/`ancho_mm` produce una
coincidencia exacta con otro producto existente (misma regla que FR-026, aplicada también en
edición — ver spec §FR-027 y Historia 4, escenario 7).

**Response 404**: producto inexistente.
