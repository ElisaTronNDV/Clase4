# Data Model: Captura de Archivo de Corte y Control de Inventario

**Input**: `spec.md` (§Key Entities, §Functional Requirements), `research.md`

**Nota de alcance**: este documento describe entidades persistentes (tablas SQLite). La
"propuesta" de datos extraídos de un PDF (Principios II/III de la constitución) **no** es una
entidad persistente — vive como respuesta HTTP transitoria entre `POST /ordenes/extraer-pdf` y
`POST /ordenes`; ver `contracts/ordenes.md`.

## Usuario

Representa una persona autenticada del sistema. Sin rol ni permisos diferenciados (FR-004).

| Campo | Tipo | Reglas |
|---|---|---|
| id | integer, PK, autoincrement | — |
| email | string, unique, not null | formato email válido; unicidad case-insensitive (FR-003) |
| password_hash | string, not null | hash bcrypt/argon2 vía passlib, nunca el password en claro (FR-005) |
| created_at | datetime, not null | default now |

No tiene relaciones salientes con otras entidades de negocio (ninguna orden ni producto queda
asociado al usuario que lo creó — el spec no pide trazabilidad de autoría, ver Assumptions).

## ConfiguracionSistema

Parámetros globales de operación. Fila única (singleton) — no hay múltiples configuraciones.

| Campo | Tipo | Reglas |
|---|---|---|
| id | integer, PK | siempre `1` (singleton) |
| margen_tolerancia_mm | float, not null | default `1.0`; MUST ser > 0, sin límite superior
  explícito (FR-029/FR-030) |
| updated_at | datetime, not null | default now, se actualiza en cada PUT |

Si la fila no existe al arrancar la aplicación, se crea con el default `1.0` (RF-17 / FR-029).

## Producto

Ítem del maestro de inventario — chapa base o recorte sobrante; el spec no los distingue como
tipos separados, solo por cómo se originan (FR-024 manual, FR-015/FR-022 automático).

| Campo | Tipo | Reglas |
|---|---|---|
| id | integer, PK, autoincrement | secuencial (FR-025); usado como criterio de desempate en FR-031 |
| material | string, not null | ej. `SAE_1010`, `INOX` |
| espesor_mm | float, not null | > 0 |
| largo_mm | float, not null | > 0 |
| ancho_mm | float, not null | > 0 |
| stock_fisico | float, not null | default `0`; puede quedar en 0 al alta automática (FR-015) |
| stock_comprometido | float, not null | default `0`; **no editable manualmente** (FR-027) — solo se
  modifica vía compromiso (FR-014) o descuento (FR-020) |
| punto_pedido | float, not null | usado para el indicador de alerta (FR-016) |
| created_at | datetime, not null | default now; ordena el desempate de FR-031 (menor Id ≈ más
  antiguo, ya que el Id es secuencial por creación) |

**Reglas de validación cruzadas**:
- Alta (FR-024/FR-026): rechazar si existe otro producto con `material`, `espesor_mm`, `largo_mm`,
  `ancho_mm` exactamente iguales (comparación exacta, no de tolerancia).
- Edición (FR-027): si la edición cambia `material`/`espesor_mm`/`largo_mm`/`ancho_mm`, se aplica
  la misma validación de unicidad exacta que en el alta, excluyendo el propio registro de la
  comparación.
- `stock_disponible` (usado en FR-016) es un valor derivado, no una columna: `stock_fisico -
  stock_comprometido`. El indicador visual de alerta (badge/ícono, FR-016) se calcula con este
  valor únicamente en el listado de productos del módulo de Inventario (`GET /api/productos`), no
  en el listado/confirmación de órdenes.

**Búsqueda de coincidencia por tolerancia** (Oficina/Taller, FR-014/FR-022/FR-023/FR-031): filtrar
por `material` y `espesor_mm` exactos, y por `largo_mm`/`ancho_mm` dentro de
`± margen_tolerancia_mm` vigente; ordenar por menor `ABS(largo_mm - x) + ABS(ancho_mm - y)`, y
como desempate por menor `id`. Ver `research.md` §4.

## OrdenTrabajo

Representa un archivo de corte confirmado por el usuario. Solo existe una vez pasado el gate de
validación humana (Principio II) — no hay estado "borrador" persistido.

| Campo | Tipo | Reglas |
|---|---|---|
| id | integer, PK, autoincrement | — |
| codigo_nest | string, unique, not null | formato fijo `NEST-######` (prefijo `NEST-` + número
  secuencial con padding a 6 dígitos, ej. `NEST-000001`), derivado del `id` autoincremental de la
  fila (FR-012, `research.md` §10) |
| estado | enum(`vigente`, `cerrada`), not null | default `vigente`; transición única
  `vigente → cerrada` (FR-019), sin camino de vuelta |
| multiplicidad | integer, not null | cantidad de chapas físicas consumidas por la orden; validado/
  editado por el usuario antes de confirmar (FR-010); usada tal cual como delta de stock
  comprometido/descontado (FR-014, FR-020) |
| espesor_mm | float, not null | — |
| material | string, not null | — |
| largo_mm | float, not null | dimensiones de la chapa de la orden |
| ancho_mm | float, not null | — |
| tiempo_ejecucion_estimado | string o duration, not null | tal como se extrae/edita del PDF |
| producto_comprometido_id | integer, FK → Producto.id, nullable | producto de chapa cuyo stock se
  comprometió (FR-014); nullable si se creó automáticamente después de advertir (FR-015) |
| created_at | datetime, not null | default now |
| closed_at | datetime, nullable | se completa al pasar a `cerrada` |

**State transitions**:

```
[creada al confirmar] --(vigente)--> [cierre en Taller, FR-019] --(cerrada)--> [fin]
```

No existe transición `cerrada → vigente` (edge case: reintentar cerrar una orden ya cerrada MUST
rechazarse, ver spec §Edge Cases).

La creación de una `OrdenTrabajo` (con sus `Pieza`/`RecorteDeclarado` y el compromiso/alta de
`Producto`) ocurre dentro de una única transacción atómica: si cualquier paso falla (incluida la
creación automática de producto de FR-015), toda la transacción revierte y ninguna fila queda
persistida (FR-015, `research.md` §11).

## Pieza

Ítem individual del listado de piezas de una orden (FR-008). No representa recortes — los
recortes ("Saved scrap") se modelan por separado como `RecorteDeclarado`, ya que tienen un ciclo
de vida distinto (afectan el maestro de productos al cerrar la orden).

| Campo | Tipo | Reglas |
|---|---|---|
| id | integer, PK, autoincrement | — |
| orden_id | integer, FK → OrdenTrabajo.id, not null | — |
| descripcion | string, not null | tal como figura en el PDF o editada por el usuario |
| cantidad | integer, not null | > 0 |

## RecorteDeclarado

Recorte sobrante detallado en una orden de trabajo (FR-009), pendiente de alta/incremento en el
maestro hasta que la orden se cierra en Taller (FR-022/FR-023) — mitigación de captura errónea:
el recorte se declara en Oficina pero solo impacta el inventario cuando el taller confirma que el
corte efectivamente se hizo.

| Campo | Tipo | Reglas |
|---|---|---|
| id | integer, PK, autoincrement | — |
| orden_id | integer, FK → OrdenTrabajo.id, not null | — |
| largo_mm | float, nullable | nullable si el nombre técnico no matcheó el patrón esperado (ver
  `research.md` §2) y el usuario no lo completó antes de confirmar — en ese caso el recorte
  MUST completarse manualmente antes de que la orden pueda cerrarse en Taller |
| ancho_mm | float, nullable | ídem |
| producto_resultante_id | integer, FK → Producto.id, nullable | se completa al cerrar la orden en
  Taller, con el producto dado de alta o incrementado (FR-022/FR-023) |

## Relaciones (resumen)

```
Usuario                     (sin relaciones a entidades de negocio)

ConfiguracionSistema        (singleton, sin relaciones)

Producto 1 ── N OrdenTrabajo.producto_comprometido_id
Producto 1 ── N RecorteDeclarado.producto_resultante_id

OrdenTrabajo 1 ── N Pieza
OrdenTrabajo 1 ── N RecorteDeclarado
```
