# Contract: Órdenes de Trabajo (Historias 2 y 3)

Todas las rutas requieren autenticación (ver `auth.md`). Cubre FR-007 a FR-023, FR-031, FR-032.

## POST /api/ordenes/extraer-pdf

Sube el archivo de corte y devuelve una **propuesta editable**, sin persistir nada (Principios II
y III de la constitución — FR-007 a FR-011).

**Request**: `multipart/form-data`, campo `archivo` (PDF).

**Response 200** (extracción completa o parcial — nunca bloquea la carga, ver `research.md` §1):
```json
{
  "multiplicidad": 1,
  "espesor_mm": 2.1,
  "material": "SAE_1010",
  "largo_mm": 3000,
  "ancho_mm": 1500,
  "tiempo_ejecucion_estimado": "00:01:22",
  "piezas": [
    { "descripcion": "string", "cantidad": 4 }
  ],
  "recortes": [
    { "largo_mm": 800, "ancho_mm": 400 },
    { "largo_mm": null, "ancho_mm": null }
  ],
  "extraccion_incompleta": false
}
```

`extraccion_incompleta: true` cuando alguna tabla esperada no se pudo extraer (edge case de PDF
con estructura inesperada) — los campos afectados vienen `null`/vacíos para que el usuario los
complete; la respuesta sigue siendo 200, nunca un error que bloquee la carga.

**Response 400**: el archivo no es un PDF válido (FR-007).

**Response 413**: el archivo supera los 20 MB (FR-007, ver Clarifications 2026-07-22 en
`spec.md`).

**Nada de esta respuesta se persiste.** El frontend retiene estos datos en estado local hasta que
el usuario los revisa, edita si hace falta, y los reenvía a `POST /api/ordenes`.

## POST /api/ordenes

Confirma la orden con los datos ya revisados/editados por el usuario (FR-010, FR-011, FR-012).
Este es el único punto donde los datos de un PDF pasan a ser persistentes.

**Request**: mismo shape que la respuesta de `extraer-pdf`, pero con todos los campos completos
(el backend rechaza si quedan campos obligatorios en `null`, incluyendo recortes con dimensiones
incompletas).

**Response 201**:
```json
{
  "id": 42,
  "codigo_nest": "NEST-000042",
  "estado": "vigente",
  "producto_comprometido": { "id": 7, "creado_automaticamente": false },
  "alerta_stock_bajo": false
}
```

- Compromete stock del producto coincidente (FR-014) usando la regla de matching de
  `data-model.md` (§Producto, coincidencia por tolerancia). El delta de stock comprometido es
  igual a `multiplicidad` (una unidad de stock por chapa física consumida, ver Clarifications
  2026-07-22 en `spec.md`).
- Si no hay coincidencia, `producto_comprometido` viene con `advertencia_producto_inexistente:
  true` y un campo `confirmar_creacion_automatica` que el cliente puede reenviar en una segunda
  llamada (o en la misma, según decisión de implementación) para aceptar la creación con stock
  físico en 0 (FR-015).
- `alerta_stock_bajo: true` si tras comprometer, `stock_fisico - stock_comprometido <=
  punto_pedido` del producto (FR-016) — informativo, no bloquea la respuesta 201; este flag solo
  alimenta el badge/ícono del listado de Inventario (`contracts/productos.md`), no se muestra en
  esta pantalla.
- `codigo_nest` sigue el formato `NEST-######` (FR-012, `research.md` §10).
- Toda la operación (orden + piezas + recortes + compromiso/alta de stock) corre en una única
  transacción atómica: si la creación automática de producto falla, la transacción entera revierte
  y no se persiste nada (FR-015, `research.md` §11) — el cliente recibe un error y puede reintentar
  con la misma propuesta ya revisada.

**Response 404** (producto no encontrado y usuario no confirmó creación automática): ver detalle
de flujo de advertencia arriba; no es necesariamente un error duro, es parte del flujo normal de
FR-015.

**Response 500**: la creación automática de producto (u otro paso de la transacción) falló;
rollback total, nada se persiste (FR-015, `research.md` §11).

## GET /api/ordenes?estado=&nest=

Listado con filtro combinable (FR-017).

**Query params**: `estado` (`vigente` | `cerrada`, opcional), `nest` (substring, opcional).

**Response 200**: `[{ "id": 1, "codigo_nest": "...", "estado": "...", "material": "...", ... }, ...]`

## GET /api/ordenes/{id}/codigo-barras

Devuelve la imagen del código de barras CODE_128 del NEST, ya verificada por decodificación
independiente antes de servirse (FR-013, ver `research.md` §5).

**Response 200**: `image/png`.

**Response 500**: si la verificación de decodificación falla, el servidor MUST tratarlo como error
de generación (no debe servir una imagen no verificada).

## GET /api/ordenes/buscar?codigo_nest=

Localiza una orden por escaneo o ingreso manual (FR-018, Historia 3).

**Response 200**: la orden completa (mismo shape que un ítem del listado, más piezas/recortes).

**Response 404**: código NEST inexistente (edge case del spec).

## POST /api/ordenes/{id}/cerrar

Finaliza una orden "vigente" (FR-019 a FR-023). Requiere conectividad activa — no hay variante
offline (FR-021, `research.md` §7); esta ruta simplemente falla como cualquier request de red sin
conexión, no necesita lógica adicional en el backend para eso.

**Response 200**:
```json
{ "id": 42, "estado": "cerrada", "closed_at": "2026-07-22T15:00:00Z" }
```

- Descuenta `stock_fisico` y `stock_comprometido` del producto comprometido (FR-020), como
  operación atómica (`research.md` §3).
- Por cada `RecorteDeclarado` de la orden: da de alta un producto nuevo si no hay coincidencia
  dentro de tolerancia (FR-022), o incrementa `stock_fisico` del producto coincidente (FR-023),
  usando la misma regla de matching que `POST /api/ordenes`.

**Response 409**: la orden ya está en estado `cerrada` (edge case — no se puede cerrar dos veces).

**Response 404**: código/id de orden inexistente.
