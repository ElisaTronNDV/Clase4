# Research: Captura de Archivo de Corte y Control de Inventario

**Input**: `plan.md` Technical Context, `.specify/memory/constitution.md`

**Nota sobre el alcance de esta investigación**: el stack tecnológico ya está fijado por
`AGENTS.md` y por la sección "Restricciones Técnicas y de Calidad de Datos" de la constitución
(Python 3.11, FastAPI, SQLite, Angular 18+, Bootstrap 5, pdfplumber, python-barcode, ZXing
ngx-scanner, passlib[bcrypt], python-jose), así que no hay decisiones de "qué tecnología usar"
pendientes. Esta investigación resuelve **cómo** usar esas piezas para cumplir los requerimientos
del spec, no **cuáles** usar.

## 1. Extracción de tablas del archivo de corte con pdfplumber

**Decision**: Usar `pdfplumber`'s `page.extract_tables()` con `table_settings` explícitos
(`vertical_strategy`/`horizontal_strategy` = `"lines"` si el PDF trae líneas de tabla reales, con
fallback a `"text"` si no las trae) para las 4 tablas del archivo de corte (Datos Generales, Datos
de Elaboración, Datos de Producción, listado de Piezas), en vez de `extract_text()` + regex sobre
todo el documento. Cada tabla se mapea por posición/encabezado conocido a un diccionario de
campos; el listado de Piezas se recorre fila por fila.

**Rationale**: `extract_tables()` con `table_settings` explícitos es más robusto ante pequeños
corrimientos de layout que un regex sobre texto plano, y falla de forma más predecible (tabla
vacía o con menos columnas de las esperadas) que un regex que puede matchear texto incorrecto
silenciosamente — algo crítico dado que el Principio III exige tratar el resultado como propuesta
y el Principio II exige que un fallo de extracción sea visible para que el usuario lo corrija, no
que se cuele silenciosamente.

**Alternatives considered**:
- Regex sobre `extract_text()` completo: descartado como estrategia principal por ser más frágil
  ante variaciones menores de espaciado; se mantiene como fallback puntual solo para el parseo del
  nombre técnico de pieza (ítem "800x400"), donde sí es apropiado un regex acotado.
- OCR (pytesseract): descartado, el PDF de Salvagnini es texto nativo, no una imagen escaneada.

**Manejo de fallo de extracción** (edge case del spec): si `extract_tables()` no encuentra las
tablas esperadas o devuelve una estructura con columnas faltantes, el endpoint de extracción
responde con un estado "extracción parcial/fallida" y campos vacíos editables, nunca un error que
bloquee la carga — el usuario completa manualmente (Historia 2, edge case 1).

## 2. Parseo de dimensiones de recorte desde el nombre técnico de pieza

**Decision**: Regex acotado `^(\d+(?:[.,]\d+)?)\s*[xX]\s*(\d+(?:[.,]\d+)?)$` aplicado solo al
campo "Pieza" de los ítems cuya descripción sea "Saved scrap", con `,` normalizado a `.` para
decimales. Si el nombre técnico no matchea el patrón, el recorte se muestra en la propuesta con
dimensiones vacías para que el usuario las complete manualmente, en vez de descartar el ítem.

**Rationale**: acota el uso de regex al único lugar del spec donde el dato no viene en una celda
de tabla estructurada sino codificado en un string libre (FR-009), consistente con la decisión de
la sección 1 de preferir extracción estructurada donde sea posible.

**Alternatives considered**: parsear como parte de `extract_tables()` (mismo mecanismo que el
resto de las piezas): descartado porque el ancho x largo no está en una columna propia, está
embebido en el nombre del ítem — requiere un paso de parseo adicional sí o sí.

## 3. Actualizaciones atómicas de stock (FR-032) en SQLite

**Decision**: Todo incremento/decremento de `stock_fisico` o `stock_comprometido` se ejecuta como
un único `UPDATE productos SET stock_x = stock_x + :delta WHERE id = :id` dentro de una
transacción corta, nunca como un `SELECT` seguido de un `UPDATE` con el valor calculado en Python.

**Rationale**: SQLite serializa escrituras (un solo writer a la vez); un `UPDATE ... SET col =
col + :delta` es atómico a nivel de esa sentencia, así que dos operaciones concurrentes (ej. una
orden de Oficina comprometiendo stock y un cierre de Taller descontándolo) se aplican una tras
otra sin perderse, sin necesidad de locking optimista/pesimista explícito — que es exactamente el
comportamiento acordado en `/speckit-clarify` (Q2: "última escritura gana" vía delta atómico, no
reemplazo de valor). Leer-luego-escribir en Python rompería esa garantía si dos requests
intercalan sus lecturas.

**Alternatives considered**: bloqueo optimista con columna de versión (descartado en clarify,
mayor complejidad para un equipo interno con volumen moderado); `BEGIN IMMEDIATE` explícito por
operación (innecesario, la sentencia UPDATE ya es atómica sin necesitar controlar el modo de
transacción manualmente).

## 4. Resolución de coincidencias (FR-031) — "coincidencia más cercana" con desempate por Id

**Decision**: La búsqueda de coincidencia por dimensiones se resuelve en una sola consulta SQL:
filtrar productos por `material` y `espesor` exactos y por `largo`/`ancho` dentro del margen de
tolerancia vigente, ordenar por `ABS(largo - :largo) + ABS(ancho - :ancho) ASC, id ASC`, y tomar el
primer resultado.

**Rationale**: el `ORDER BY` con dos claves reproduce exactamente la regla acordada (menor
diferencia de dimensiones; empate exacto → menor Id) en una sola operación determinística, sin
lógica de desempate separada en el código de aplicación que podría desincronizarse de la regla
documentada en el spec.

**Alternatives considered**: traer todos los candidatos a Python y ordenar ahí — descartado, es
estrictamente más código para el mismo resultado y separa la regla de negocio de donde se decide.

## 5. Generación y verificación de código de barras (FR-013, RNF-06)

**Decision**: Generar el código de barras del NEST con `python-barcode`, formato CODE_128,
`module_width >= 0.33mm` y writer options que respeten la relación de aspecto real de la imagen
resultante (sin forzar un ancho/alto fijo). Como parte del mismo flujo (no como paso manual
posterior), decodificar la imagen generada con `pyzbar`/`zbar` a una resolución equivalente a
impresión típica (≥300 DPI) antes de servirla; si no decodifica, se trata como error de generación,
no como una imagen "que se ve bien".

**Rationale**: implementa directamente la restricción de la constitución ("no dar por buena la
generación de un código de barras solo porque produce una imagen") y el AC del spec/PRD que exige
que el código sea decodificable por un lector estándar, no solo reconocible visualmente.

**Alternatives considered**: verificar el código de barras manualmente en QA sin automatizarlo —
descartado, no es repetible y viola el principio de Test-First (la verificación debe poder
ejecutarse como test automatizado en cada build).

## 6. Sesión y expiración (FR-006, RNF-05)

**Decision**: JWT (python-jose) con claim `exp` a 24 h desde la emisión, validado en cada request
vía dependencia de FastAPI; sin refresh token ni renovación silenciosa — al expirar, el frontend
recibe 401 y redirige a login (consistente con FR-002, no hay modo "sesión indefinida").

**Rationale**: es la implementación más simple que cumple RNF-05 tal cual está escrito ("la sesión
debe expirar tras 24 h de inactividad" interpretado como 24 h desde el login, dado que no hay
requerimiento explícito de extender la sesión por actividad); evita la complejidad de manejar
refresh tokens para un sistema de uso interno.

**Alternatives considered**: sliding expiration (renovar `exp` en cada request) — no descartado
por mala práctica, sino porque el spec no pide explícitamente extender la sesión por actividad y
agregarlo sería una decisión de producto no solicitada; queda como posible mejora futura, no como
parte de este plan.

## 7. Guardia de conectividad en Taller (FR-021)

**Decision**: El frontend Angular no implementa ningún cacheo/cola offline para el módulo de
Taller; cada acción (buscar por NEST, cerrar orden) es una llamada HTTP directa, y un fallo de red
(sin respuesta / timeout) se muestra como error bloqueante, no se reintenta en background.

**Rationale**: implementa literalmente la decisión de `/speckit-clarify` (Q3: "requiere conexión
siempre, sin modo offline ni sincronización posterior"); agregar un service worker u otra capa de
cacheo sería contradecir esa decisión explícita.

## 8. Autenticación de escaneo — formato del scanner (RF-08, constitución)

**Decision**: El componente `ngx-scanner` en la pantalla de Taller se configura explícitamente con
`formats: [BarcodeFormat.CODE_128]` (no se deja el default de la librería).

**Rationale**: la constitución señala explícitamente que ZXing/ngx-scanner por default solo
soporta QR y que hay que fijar el formato esperado o el scanner no detecta nada aunque cámara y
permisos funcionen bien.

## 9. Estrategia de testing (Principio I — Test-First)

**Decision**:
- Backend: `pytest` + `TestClient` de FastAPI contra una base SQLite temporal por test (fixture
  que crea y destruye el archivo), sin mocks de la base de datos real (coincide con el patrón ya
  usado en otras integraciones del equipo: tests de integración contra una base real, no mockeada).
- Frontend: `ng test` (Jasmine/Karma) para componentes y servicios; los flujos que cruzan
  componentes (ej. subir PDF → revisar → confirmar) se cubren con tests de integración de
  componente, no E2E en esta fase.
- Cada FR del spec debe tener al menos un test de contrato/integración que lo cubra antes de
  implementarlo (Principio I y sección "Flujo de Desarrollo y Calidad" de la constitución); esto se
  traduce en tareas de test explícitas por historia de usuario en `/speckit-tasks`.

**Rationale**: cumple directamente el Principio I (NON-NEGOTIABLE) y evita el riesgo señalado en su
rationale (stock incorrecto, duplicados, órdenes mal generadas por regresiones no detectadas).

## 10. Generación del código NEST (FR-012)

**Decision**: `codigo_nest` se genera como `f"NEST-{n:06d}"`, donde `n` es un contador secuencial
obtenido dentro de la misma transacción que inserta la fila de `OrdenTrabajo` (ej.
`SELECT COALESCE(MAX(id), 0) + 1` sobre `orden_trabajo` o un `INSERT` que deja que SQLite asigne el
`id` autoincremental y luego formatea `codigo_nest` a partir de ese mismo `id`), nunca calculado en
una consulta separada previa al insert que pueda desincronizarse bajo escritura concurrente.

**Rationale**: usar el propio `id` autoincremental de la fila recién insertada como base del NEST
evita una carrera entre "leer el próximo número" y "escribir la fila" (el mismo problema que
motivó la decisión de la sección 3 para stock); SQLite garantiza que el `id` asignado es único y
secuencial sin lógica adicional. El formato fijo (`NEST-` + 6 dígitos con padding) fue definido en
`/speckit-clarify` del 2026-07-22.

**Alternatives considered**: tabla de contador separada con su propio lock — descartada, agrega
complejidad y una segunda fuente de verdad para un número que el autoincrement de `orden_trabajo`
ya provee.

## 11. Transacción atómica de confirmación de orden (FR-015)

**Decision**: `POST /api/ordenes` ejecuta el insert de `OrdenTrabajo` + `Pieza`(s) +
`RecorteDeclarado`(s) + el compromiso de stock (`aplicar_delta_stock`) + la creación automática de
producto (si el usuario la confirmó) dentro de una única transacción de base de datos. Si
cualquier paso falla — incluida la creación automática del producto — toda la transacción hace
rollback y el endpoint responde con un error (nada queda persistido).

**Rationale**: implementa literalmente la decisión de `/speckit-clarify` del 2026-07-22
("todo-o-nada" si falla la creación automática de producto), y es consistente con los Principios
II/III de la constitución: una orden nunca debe quedar persistida en un estado a medias (ej. orden
guardada pero sin producto comprometido resuelto).

**Alternatives considered**: guardar la orden igual y marcar el producto como "pendiente de
resolución manual" — descartado explícitamente en `/speckit-clarify` a favor del rollback total.

## Resumen de NEEDS CLARIFICATION resueltos

Ninguno pendiente: el stack está fijado por la constitución. Las ambigüedades de comportamiento
resueltas en `/speckit-clarify` incluyen, del 2026-07-21: desempate de match (FR-031), concurrencia
(FR-032), conectividad offline (FR-021); y del 2026-07-22: regla de contraseña (FR-003), formato
del NEST (FR-012, ver sección 10), límites del margen de tolerancia (FR-029), ausencia de bloqueo
de login, límite de tamaño de PDF (FR-007), definición de multiplicidad (FR-014), rollback
todo-o-nada en fallo de alta automática (FR-015, ver sección 11), criterio del indicador de alerta
(FR-016), metodología de medición de SC-001, y alcance de la conectividad obligatoria a todos los
módulos (FR-021).
