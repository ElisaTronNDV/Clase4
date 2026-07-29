---

description: "Task list for Captura de Archivo de Corte y Control de Inventario"
---

# Tasks: Captura de Archivo de Corte y Control de Inventario

**Input**: Design documents from `/specs/001-captura-corte-inventario/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Per la constitución del proyecto (Principio I, Test-First, NON-NEGOTIABLE), las tareas
de test son OBLIGATORIAS para cada historia de usuario — se escriben primero y deben fallar antes
de implementar (ciclo Red-Green-Refactor).

**Organization**: Tareas agrupadas por historia de usuario (spec.md), en orden de prioridad
P1→P5, para que cada una sea implementable y testeable de forma independiente.

**Nota de esta revisión**: regenerado tras dos sesiones de `/speckit-clarify` (2026-07-22) y el
refresh de `/speckit-plan` correspondiente. Cambios respecto a la versión anterior: validación de
tamaño máximo de PDF (413, FR-007), generación de código NEST con formato fijo (T033/T042),
transacción atómica de confirmación de orden con rollback total (T046), manejo de advertencia de
producto inexistente en la UI (T050), documento imprimible con detalle de piezas (T052, cierra un
gap detectado en `/speckit-analyze`), e indicador visual de alerta de stock bajo en el listado de
Inventario (T067/T070, también cierra un gap de `/speckit-analyze`, ahora explícitamente scoped a
Inventario y no a Oficina).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Puede ejecutarse en paralelo (archivos distintos, sin dependencias pendientes)
- **[Story]**: Historia de usuario a la que pertenece (US1..US5, según spec.md)
- Cada tarea incluye la ruta de archivo exacta

## Path Conventions

Aplicación web (ver `plan.md` § Project Structure): `backend/app/`, `backend/tests/`,
`frontend/src/app/`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Inicialización del proyecto backend y frontend.

- [X] T001 Crear estructura de directorios backend (`backend/app/core`, `backend/app/db`,
  `backend/app/models`, `backend/app/schemas`, `backend/app/services`, `backend/app/api`,
  `backend/tests/contract`, `backend/tests/integration`, `backend/tests/unit`) según
  `plan.md` § Project Structure
- [X] T002 [P] Crear `backend/requirements.txt` con fastapi, uvicorn, sqlalchemy, pdfplumber,
  python-barcode, pyzbar, passlib[bcrypt], python-jose, python-multipart, pytest, httpx
- [X] T003 [P] Crear `backend/.env.example` con `SECRET_KEY` como variable obligatoria sin valor
  por default, según `AGENTS.md`
- [X] T004 Crear proyecto Angular 18+ en `frontend/` con routing habilitado; agregar Bootstrap 5 y
  ZXing ngx-scanner como dependencias (`AGENTS.md` § Cómo correr)
- [X] T005 [P] Crear módulos de feature vacíos en `frontend/src/app/auth/`,
  `frontend/src/app/oficina/`, `frontend/src/app/taller/`, `frontend/src/app/inventario/`,
  `frontend/src/app/configuracion/`, `frontend/src/app/shared/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Infraestructura común que TODAS las historias de usuario necesitan antes de poder
implementarse.

**⚠️ CRITICAL**: Ninguna historia de usuario puede empezar hasta que esta fase esté completa.

- [X] T006 Implementar `backend/app/core/config.py` — carga `SECRET_KEY` y demás configuración
  únicamente desde variables de entorno (Principio IV / RNF-05; nunca hardcodear secretos)
- [X] T007 Implementar `backend/app/db/session.py` — engine y sesión SQLAlchemy sobre SQLite,
  `Base` declarativa, creación de la base vacía en el primer arranque
- [X] T008 [P] Implementar `backend/app/core/security.py` — `hash_password`/`verify_password`
  (passlib bcrypt) y `create_access_token`/`decode_access_token` (python-jose, JWT con `exp` a
  24 h, `research.md` §6, Principio IV) — FR-005, FR-006
- [X] T009 Implementar `backend/app/main.py` — instancia FastAPI, registro de routers (placeholder),
  CORS, manejo global de errores (404/422/409/413/500 sin filtrar detalles internos)
- [X] T010 [P] Implementar `backend/app/models/configuracion_sistema.py` (tabla singleton) y
  evento de arranque que siembra la fila con `margen_tolerancia_mm=1.0` si no existe (FR-029)
- [X] T011 [P] Implementar `frontend/src/app/app.routes.ts` — esqueleto de rutas `/login`,
  `/oficina`, `/taller`, `/inventario`, `/configuracion` (sin guard todavía)
- [X] T012 [P] Implementar `frontend/src/app/shared/services/api.service.ts` — wrapper de
  `HttpClient` con URL base configurable
- [X] T013 Implementar `frontend/src/app/shared/interceptors/auth.interceptor.ts` — agrega el
  header `Authorization: Bearer <token>` a cada request y redirige a `/login` ante un 401 (FR-002)

**Checkpoint**: Infraestructura lista — las historias de usuario pueden empezar (en paralelo, si
hay capacidad, o en orden de prioridad).

---

## Phase 3: User Story 1 - Acceso seguro al sistema (Priority: P1) 🎯 MVP

**Goal**: Login, autorregistro y protección de todas las rutas del sistema (FR-001 a FR-006).

**Independent Test**: Crear una cuenta nueva, cerrar sesión, iniciar sesión con esas credenciales,
verificar que las rutas del sistema quedan bloqueadas sin sesión y accesibles con sesión.

### Tests for User Story 1 (MANDATORY — write first, must fail before implementation) ⚠️

- [X] T014 [P] [US1] Contract test `POST /api/auth/registro` (incluye 409 email duplicado, 422
  password con menos de 8 caracteres — FR-003, sin exigir mayúscula/número/símbolo) en
  `backend/tests/contract/test_auth_registro.py` — `contracts/auth.md`
- [X] T015 [P] [US1] Contract test `POST /api/auth/login` (incluye 401 credenciales inválidas, sin
  bloqueo de cuenta tras múltiples intentos fallidos, JWT con `exp` a 24h) en
  `backend/tests/contract/test_auth_login.py` — `contracts/auth.md`
- [X] T016 [P] [US1] Integration test: acceso a una ruta protegida sin token → 401; con token
  válido → acceso concedido a todos los módulos sin restricción de rol (FR-001, FR-002, FR-004) en
  `backend/tests/integration/test_auth_flow.py`

### Implementation for User Story 1

- [X] T017 [P] [US1] Crear modelo `Usuario` en `backend/app/models/usuario.py` (email unique,
  password_hash) — `data-model.md` § Usuario
- [X] T018 [P] [US1] Crear schemas pydantic `UsuarioCreate` (password `min_length=8`, sin otro
  requisito de composición), `UsuarioLogin`, `UsuarioOut`, `Token` en `backend/app/schemas/auth.py`
  — `contracts/auth.md`, FR-003
- [X] T019 [US1] Implementar `POST /api/auth/registro` en `backend/app/api/auth.py` (hashea
  password, rechaza email duplicado con 409) (depende de T017, T018, T008) — FR-003
- [X] T020 [US1] Implementar `POST /api/auth/login` en `backend/app/api/auth.py` (verifica
  password, emite JWT; sin mecanismo de bloqueo/rate limiting ante fallos repetidos — Clarifications
  2026-07-22) (depende de T017, T018, T008) — FR-005
- [X] T021 [US1] Implementar dependencia `get_current_user` en `backend/app/core/security.py`
  (401 ante token ausente/inválido/expirado), lista para usarse en todos los routers protegidos
  (FR-002, FR-004) (depende de T008)
- [X] T021a [P] [US1] Implementar `frontend/src/app/auth/auth-token.service.ts` — helper
  compartido para guardar/leer/borrar el token de sesión persistido, usado por login, logout y el
  guard/interceptor (FR-006a)
- [X] T022 [P] [US1] Implementar `frontend/src/app/auth/login/login.component.ts` — formulario
  email/password, llama a `POST /auth/login`, persiste el token vía `auth-token.service` (depende
  de T021a)
- [X] T023 [P] [US1] Implementar `frontend/src/app/auth/registro/registro.component.ts` —
  formulario de alta con validación de mínimo 8 caracteres en el password, maneja el error 409 de
  email duplicado
- [X] T024 [US1] Implementar `frontend/src/app/auth/auth.guard.ts` — `CanActivate` que redirige a
  `/login` si no hay token válido (FR-002) (depende de T021a)
- [X] T024a [US1] Implementar acción de "Cerrar sesión" (`frontend/src/app/auth/logout/logout.component.ts`
  o botón equivalente en un layout compartido) que borra el token vía `auth-token.service` y
  redirige a `/login` (FR-006a) (depende de T021a)
- [X] T025 [US1] Aplicar `auth.guard` a las rutas `/oficina`, `/taller`, `/inventario`,
  `/configuracion` en `frontend/src/app/app.routes.ts` (depende de T011, T024)

**Checkpoint**: User Story 1 funcional y testeable de forma independiente.

---

## Phase 4: User Story 2 - Captura del archivo de corte y generación de orden de trabajo (Priority: P2)

**Goal**: Subir PDF → propuesta editable → confirmar → NEST + compromiso de stock + impresión con
código de barras verificado + listado/filtro de órdenes (FR-007 a FR-017, FR-031, FR-032).

**Independent Test**: Subir un PDF de ejemplo, validar/editar los datos extraídos, confirmar,
verificar NEST generado, orden "vigente" y stock comprometido según multiplicidad.

### Tests for User Story 2 (MANDATORY — write first, must fail before implementation) ⚠️

- [X] T026 [P] [US2] Contract test `POST /api/ordenes/extraer-pdf` (PDF inválido → 400; archivo de
  más de 20 MB → 413, FR-007; PDF con tabla faltante → `extraccion_incompleta: true`, nunca error
  bloqueante; incluir aserción de que no se crea ninguna fila en
  `OrdenTrabajo`/`Pieza`/`RecorteDeclarado` tras la llamada, SC-006) en
  `backend/tests/contract/test_ordenes_extraer_pdf.py` — `contracts/ordenes.md`
- [X] T027 [P] [US2] Contract test `POST /api/ordenes` (compromiso de stock == multiplicidad,
  formato de `codigo_nest` = `NEST-######`, advertencia de producto inexistente + alta automática,
  alerta de stock bajo, y rollback total —ninguna fila persiste— si la creación automática del
  producto falla, FR-015/`research.md` §11) en `backend/tests/contract/test_ordenes_crear.py` —
  `contracts/ordenes.md`
- [X] T028 [P] [US2] Contract test `GET /api/ordenes` (filtro por estado + búsqueda parcial por
  NEST, combinables) en `backend/tests/contract/test_ordenes_listar.py` — FR-017
- [X] T029 [P] [US2] Contract test `GET /api/ordenes/{id}/codigo-barras` (la imagen debe decodificar
  con pyzbar antes de servirse) en `backend/tests/contract/test_ordenes_codigo_barras.py` —
  FR-013, RNF-06
- [X] T030 [P] [US2] Unit test del servicio de extracción de PDF (tablas completas, tabla
  faltante, parseo de nombre técnico de recorte "800x400" y variantes con decimales/mayúsculas) en
  `backend/tests/unit/test_pdf_extraction.py` — `research.md` §1-2
- [X] T031 [P] [US2] Unit test de matching por tolerancia con desempate por menor Id en empate
  exacto en `backend/tests/unit/test_stock_matching.py` — FR-031, `research.md` §4
- [X] T032 [P] [US2] Unit test de actualización atómica de stock ante deltas concurrentes en
  `backend/tests/unit/test_stock_atomic.py` — FR-032, `research.md` §3
- [X] T033 [P] [US2] Unit test de generación de código NEST (formato `NEST-######` derivado del id
  autoincremental, sin colisión bajo ids sucesivos) en
  `backend/tests/unit/test_nest_generation.py` — FR-012, `research.md` §10
- [X] T034 [P] [US2] Integration test del flujo completo de Historia 2 (subir PDF → editar
  propuesta → confirmar → NEST + stock comprometido) en
  `backend/tests/integration/test_oficina_flow.py`

### Implementation for User Story 2

- [X] T035 [P] [US2] Crear modelo `Producto` en `backend/app/models/producto.py` —
  `data-model.md` § Producto
- [X] T036 [P] [US2] Crear modelo `OrdenTrabajo` en `backend/app/models/orden_trabajo.py`
  (`codigo_nest` string único, formato `NEST-######`) — `data-model.md` § OrdenTrabajo
- [X] T037 [P] [US2] Crear modelo `Pieza` en `backend/app/models/pieza.py` — `data-model.md` § Pieza
- [X] T038 [P] [US2] Crear modelo `RecorteDeclarado` en `backend/app/models/recorte_declarado.py`
  — `data-model.md` § RecorteDeclarado
- [X] T039 [US2] Implementar servicio de extracción de PDF en
  `backend/app/services/pdf_extraction.py` (pdfplumber `extract_tables` + regex acotado para
  recortes) — `research.md` §1-2 (hace pasar T030) — FR-008, FR-009
- [X] T040 [US2] Implementar búsqueda de producto coincidente con tolerancia y desempate en
  `backend/app/services/stock.py` (función `buscar_producto_coincidente`) — `research.md` §4 (hace
  pasar T031)
- [X] T041 [US2] Implementar actualización atómica de stock en `backend/app/services/stock.py`
  (función `aplicar_delta_stock`, un único `UPDATE ... SET col = col + :delta`, delta = multiplicidad
  para compromiso/descuento de chapa) — `research.md` §3 (hace pasar T032)
- [X] T042 [US2] Implementar generación de código NEST en `backend/app/services/ordenes.py`
  (función `generar_codigo_nest`, formato `f"NEST-{id:06d}"` a partir del id autoincremental de la
  fila recién insertada, sin consulta previa separada que pueda desincronizarse) — `research.md`
  §10 (hace pasar T033) — FR-012
- [X] T043 [P] [US2] Implementar servicio de generación y verificación de código de barras en
  `backend/app/services/barcode.py` (python-barcode CODE_128, `module_width >= 0.33mm`,
  verificación con pyzbar antes de servir) — `research.md` §5
- [X] T044 [P] [US2] Crear schemas pydantic `PropuestaExtraccion`, `OrdenCreate`, `OrdenOut`
  (incluye `alerta_stock_bajo`, `advertencia_producto_inexistente`,
  `confirmar_creacion_automatica`), `PiezaSchema`, `RecorteSchema` en
  `backend/app/schemas/ordenes.py` — `contracts/ordenes.md` — FR-010, FR-011
- [X] T045 [US2] Implementar `POST /api/ordenes/extraer-pdf` en `backend/app/api/ordenes.py`
  (valida tamaño máximo 20 MB → 413 antes de parsear) (depende de T039, T044) — FR-007, FR-010,
  FR-011
- [X] T046 [US2] Implementar `POST /api/ordenes` en `backend/app/api/ordenes.py` como una única
  transacción atómica (orden + piezas + recortes + compromiso de stock vía T040/T041 + alta
  automática de producto si corresponde): si cualquier paso falla —incluida la creación automática
  del producto— toda la transacción revierte y no se persiste nada (FR-015, `research.md` §11);
  usa T042 para `codigo_nest`, compromete stock en una cantidad igual a la multiplicidad (FR-012,
  FR-014), advertencia + alta automática si no hay coincidencia (FR-015), alerta de stock bajo
  (FR-016) (depende de T035-T038, T040, T041, T042, T044, T045)
- [X] T047 [US2] Implementar `GET /api/ordenes` (filtro estado + búsqueda NEST) en
  `backend/app/api/ordenes.py` — FR-017 (depende de T036)
- [X] T048 [US2] Implementar `GET /api/ordenes/{id}/codigo-barras` en `backend/app/api/ordenes.py`
  (depende de T043, T046)
- [X] T049 [P] [US2] Implementar `frontend/src/app/oficina/subir-pdf/subir-pdf.component.ts` —
  sube el PDF, llama a `extraer-pdf`, muestra la propuesta editable sin persistir nada (Principios
  II/III), maneja el error 413 de archivo mayor a 20 MB
- [X] T050 [US2] Implementar
  `frontend/src/app/oficina/revisar-orden/revisar-orden.component.ts` — formulario editable de la
  propuesta (datos generales, piezas, recortes), botón confirmar → `POST /api/ordenes`; si la
  respuesta trae `advertencia_producto_inexistente`, muestra el aviso y un botón para reenviar la
  confirmación con `confirmar_creacion_automatica` (FR-015) (depende de T046, T049)
- [X] T051 [P] [US2] Implementar
  `frontend/src/app/oficina/listado-ordenes/listado-ordenes.component.ts` — listado con filtro de
  estado y búsqueda por NEST (FR-017)
- [X] T052 [US2] Implementar
  `frontend/src/app/oficina/orden-impresion/orden-impresion.component.ts` — combina la imagen de
  código de barras (`GET /ordenes/{id}/codigo-barras`) con el detalle de piezas de la orden en una
  vista imprimible y expone una acción "Imprimir" (`window.print()`) (FR-013) (depende de T048,
  T050)
- [X] T053 [US2] Registrar las rutas de Oficina en `frontend/src/app/app.routes.ts`, protegidas por
  `auth.guard` (depende de T025, T049, T050, T051, T052)

**Checkpoint**: User Stories 1 y 2 funcionan de forma independiente.

---

## Phase 5: User Story 3 - Cierre de la orden en taller y descuento de stock (Priority: P3)

**Goal**: Localizar la orden por escaneo o NEST manual, cerrarla, descontar stock consumido y dar
de alta/incrementar los recortes declarados (FR-018 a FR-023).

**Independent Test**: Partiendo de una orden "vigente", escanear/ingresar su NEST, verificar que
se muestra, finalizarla y comprobar el descuento de stock y el alta/incremento de recortes.

### Tests for User Story 3 (MANDATORY — write first, must fail before implementation) ⚠️

- [X] T054 [P] [US3] Contract test `GET /api/ordenes/buscar?codigo_nest=` (incluye 404 código
  inexistente) en `backend/tests/contract/test_ordenes_buscar.py` — FR-018
- [X] T055 [P] [US3] Contract test `POST /api/ordenes/{id}/cerrar` (incluye 409 orden ya cerrada,
  descuento de stock físico/comprometido == multiplicidad, alta de recorte sin coincidencia,
  incremento de recorte con coincidencia) en `backend/tests/contract/test_ordenes_cerrar.py` —
  FR-019 a FR-023
- [X] T056 [P] [US3] Integration test del flujo completo de Historia 3 (escanear → mostrar orden →
  cerrar → verificar descuento y recortes) en `backend/tests/integration/test_taller_flow.py`

### Implementation for User Story 3

- [X] T057 [US3] Implementar `GET /api/ordenes/buscar` en `backend/app/api/ordenes.py` (depende de
  T036)
- [X] T058 [US3] Implementar `POST /api/ordenes/{id}/cerrar` en `backend/app/api/ordenes.py`
  (descuenta stock vía `aplicar_delta_stock` T041, resuelve alta/incremento de recorte vía
  `buscar_producto_coincidente` T040) (depende de T040, T041, T057) — FR-020, FR-022, FR-023
- [X] T059 [P] [US3] Implementar
  `frontend/src/app/taller/escanear-orden/escanear-orden.component.ts` — integra ngx-scanner
  configurado explícitamente con `formats: [CODE_128]` (constitución) + input manual de NEST
  (FR-018)
- [X] T060 [US3] Implementar `frontend/src/app/taller/cerrar-orden/cerrar-orden.component.ts` —
  muestra la orden encontrada, botón finalizar → `POST .../cerrar`, muestra error bloqueante sin
  reintento automático ante falla de conectividad (FR-021) (depende de T059)
- [X] T061 [US3] Registrar las rutas de Taller en `frontend/src/app/app.routes.ts`, protegidas por
  `auth.guard` (depende de T025, T059, T060)

**Checkpoint**: User Stories 1, 2 y 3 funcionan de forma independiente.

---

## Phase 6: User Story 4 - Gestión manual del maestro de productos (Priority: P4)

**Goal**: Alta, edición y listado manual de productos en el maestro de inventario (FR-024 a
FR-028), incluyendo el indicador visual de alerta de stock bajo (FR-016).

**Independent Test**: Dar de alta un producto con datos válidos, editar un campo permitido y
consultar el listado completo (verificando el indicador de alerta cuando corresponda), sin
depender de ninguna orden de trabajo.

### Tests for User Story 4 (MANDATORY — write first, must fail before implementation) ⚠️

- [X] T062 [P] [US4] Contract test `POST /api/productos` (incluye 422 campo obligatorio faltante,
  409 duplicado exacto) en `backend/tests/contract/test_productos_crear.py` — FR-024, FR-025,
  FR-026
- [X] T063 [P] [US4] Contract test `GET /api/productos` (incluye `alerta_stock_bajo: true` cuando
  `stock_fisico - stock_comprometido <= punto_pedido`, FR-016) en
  `backend/tests/contract/test_productos_listar.py` — FR-028
- [X] T064 [P] [US4] Contract test `PUT /api/productos/{id}` (stock_comprometido no editable, 409
  ante colisión exacta al editar material/espesor/dimensiones) en
  `backend/tests/contract/test_productos_editar.py` — FR-027

### Implementation for User Story 4

- [X] T065 [P] [US4] Crear schemas pydantic `ProductoCreate`, `ProductoOut` (incluye
  `alerta_stock_bajo`), `ProductoUpdate` en `backend/app/schemas/productos.py` —
  `contracts/productos.md`
- [X] T066 [US4] Implementar `POST /api/productos` en `backend/app/api/productos.py` (valida
  unicidad exacta, FR-026) (depende de T035, T065)
- [X] T067 [US4] Implementar `GET /api/productos` en `backend/app/api/productos.py` — FR-028,
  calcula `alerta_stock_bajo` por producto (`stock_fisico - stock_comprometido <= punto_pedido`,
  FR-016) (depende de T035)
- [X] T068 [US4] Implementar `PUT /api/productos/{id}` en `backend/app/api/productos.py` (excluye
  `stock_comprometido`, valida unicidad exacta al editar dimensiones, FR-027) (depende de T066)
- [ ] T069 [P] [US4] Implementar
  `frontend/src/app/inventario/alta-producto/alta-producto.component.ts` — formulario de alta con
  validación de campos obligatorios (FR-024)
- [ ] T070 [P] [US4] Implementar
  `frontend/src/app/inventario/listado-productos/listado-productos.component.ts` — listado
  completo del maestro (FR-028) con badge/ícono de alerta junto al stock cuando
  `alerta_stock_bajo` es `true` (FR-016; este indicador aparece únicamente en este listado, no en
  Oficina)
- [ ] T071 [US4] Implementar
  `frontend/src/app/inventario/editar-producto/editar-producto.component.ts` — formulario de
  edición con el campo de stock comprometido bloqueado (FR-027) (depende de T069)
- [ ] T072 [US4] Registrar las rutas de Inventario en `frontend/src/app/app.routes.ts`, protegidas
  por `auth.guard` (depende de T025, T069, T070, T071)

**Checkpoint**: User Stories 1 a 4 funcionan de forma independiente.

---

## Phase 7: User Story 5 - Configuración del margen de tolerancia dimensional (Priority: P5)

**Goal**: Consultar y ajustar el margen de tolerancia dimensional usado por las búsquedas de
coincidencia de Oficina y Taller (FR-029, FR-030).

**Independent Test**: Consultar el valor por defecto, modificarlo y verificar que una búsqueda de
coincidencia (Historia 2 o 3) usa el nuevo valor configurado.

### Tests for User Story 5 (MANDATORY — write first, must fail before implementation) ⚠️

- [ ] T073 [P] [US5] Contract test `GET /api/configuracion` (devuelve `1.0` por default) en
  `backend/tests/contract/test_configuracion_get.py` — FR-029
- [ ] T074 [P] [US5] Contract test `PUT /api/configuracion` (422 valor no positivo —cero o
  negativo—, sin límite superior explícito; un nuevo valor cambia el resultado de
  `buscar_producto_coincidente` de US2/US3) en
  `backend/tests/contract/test_configuracion_put.py` — FR-030

### Implementation for User Story 5

- [ ] T075 [P] [US5] Crear schemas pydantic `ConfiguracionOut`, `ConfiguracionUpdate` (valida solo
  `> 0`, sin cota superior) en `backend/app/schemas/configuracion.py` — `contracts/configuracion.md`
- [ ] T076 [US5] Implementar `GET /api/configuracion` en `backend/app/api/configuracion.py`
  (depende de T010, T075)
- [ ] T077 [US5] Implementar `PUT /api/configuracion` en `backend/app/api/configuracion.py`
  (depende de T076)
- [ ] T078 [P] [US5] Implementar
  `frontend/src/app/configuracion/margen-tolerancia/margen-tolerancia.component.ts` —
  mostrar/editar el margen (FR-029, FR-030)
- [ ] T079 [US5] Registrar la ruta de Configuración en `frontend/src/app/app.routes.ts`, protegida
  por `auth.guard` (depende de T025, T078)

**Checkpoint**: Las 5 historias de usuario funcionan de forma independiente.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Mejoras que afectan a varias historias de usuario, previas al cierre de la feature.

- [ ] T080 [P] Documentar el mapa FR → test (qué archivo de test cubre cada FR-001..FR-032,
  incluidas las clarificaciones de las sesiones 2026-07-21 y 2026-07-22) en
  `specs/001-captura-corte-inventario/` — constitución § Flujo de Desarrollo y Calidad
- [ ] T081 [P] Revisar accesibilidad básica de los formularios (labels asociados, orden de foco,
  navegación por teclado) en `frontend/src/app/**/*.component.html`
- [ ] T082 Ejecutar `pytest` y `ng test` completos y confirmar 0 fallos (gate de la constitución
  antes de cerrar la feature)
- [ ] T083 Ejecutar `quickstart.md` de punta a punta manualmente con un PDF real de
  `Archivos de Corte/`
- [ ] T084 [P] Revisar el manejo de excepciones no capturadas en `backend/app/main.py` (deben
  devolver 500 genérico sin filtrar detalles internos)
- [ ] T085 [P] Medir accuracy de extracción **por campo individual** (≥98%, SC-001, metodología
  fijada en Clarifications 2026-07-22) y latencia de extracción/listados (SC-002 <10s, SC-003 <2s
  p95) contra una muestra de PDFs de `Archivos de Corte/` en
  `backend/tests/performance/test_metrics.py`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sin dependencias — puede iniciar de inmediato
- **Foundational (Phase 2)**: depende de Setup — BLOQUEA a las 5 historias de usuario
- **User Stories (Phase 3-7)**: todas dependen de Foundational; entre sí, cada una puede
  implementarse en paralelo o en orden de prioridad (US1 → US2 → US3 → US4 → US5)
- **Polish (Phase 8)**: depende de que las historias que se quieran entregar estén completas

### User Story Dependencies

- **US1 (P1)**: solo depende de Foundational — es el punto de entrada obligatorio, pero no
  bloquea el desarrollo (no la ejecución en runtime) de las demás historias
- **US2 (P2)**: depende de Foundational; usa el modelo `Producto` que crea (T035), no depende de
  US4 aunque comparta la tabla
- **US3 (P3)**: depende de Foundational y de los modelos/servicios creados en US2 (`OrdenTrabajo`,
  `Producto`, `buscar_producto_coincidente`, `aplicar_delta_stock`) — en la práctica se implementa
  después de US2, aunque conceptualmente es una historia separada
- **US4 (P4)**: depende de Foundational y del modelo `Producto` creado en US2 (T035); las rutas
  CRUD de Inventario son independientes de las de Oficina/Taller
- **US5 (P5)**: depende de Foundational (tabla `ConfiguracionSistema`, T010); su efecto solo es
  observable si US2/US3 ya implementaron el matching que la consume

### Within Each User Story

- Tests MUST escribirse y fallar antes de implementar (Principio I)
- Modelos antes que servicios; servicios antes que endpoints; endpoints antes que UI
- Historia completa y verificada en su Checkpoint antes de pasar a la siguiente prioridad

### Parallel Opportunities

- Todas las tareas [P] de Setup pueden correr en paralelo
- Todas las tareas [P] de Foundational pueden correr en paralelo
- Una vez completada Foundational, US1 puede empezar; US2-US5 pueden empezar en paralelo si hay
  capacidad, aunque US3/US4/US5 reutilizan modelos creados en US2 (ver Dependencies arriba)
- Dentro de cada historia, todos los tests marcados [P] pueden correr en paralelo entre sí
- Los modelos de una misma historia marcados [P] pueden crearse en paralelo

---

## Parallel Example: User Story 2

```bash
# Lanzar todos los tests de la Historia 2 juntos (deben fallar antes de implementar):
Task: "Contract test POST /api/ordenes/extraer-pdf en backend/tests/contract/test_ordenes_extraer_pdf.py"
Task: "Contract test POST /api/ordenes en backend/tests/contract/test_ordenes_crear.py"
Task: "Contract test GET /api/ordenes en backend/tests/contract/test_ordenes_listar.py"
Task: "Contract test GET /api/ordenes/{id}/codigo-barras en backend/tests/contract/test_ordenes_codigo_barras.py"
Task: "Unit test extracción PDF en backend/tests/unit/test_pdf_extraction.py"
Task: "Unit test matching por tolerancia en backend/tests/unit/test_stock_matching.py"
Task: "Unit test update atómico de stock en backend/tests/unit/test_stock_atomic.py"
Task: "Unit test generación de código NEST en backend/tests/unit/test_nest_generation.py"

# Lanzar los modelos de la Historia 2 juntos:
Task: "Crear modelo Producto en backend/app/models/producto.py"
Task: "Crear modelo OrdenTrabajo en backend/app/models/orden_trabajo.py"
Task: "Crear modelo Pieza en backend/app/models/pieza.py"
Task: "Crear modelo RecorteDeclarado en backend/app/models/recorte_declarado.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 solamente)

1. Completar Phase 1: Setup
2. Completar Phase 2: Foundational (crítico — bloquea todas las historias)
3. Completar Phase 3: User Story 1
4. **DETENER Y VALIDAR**: probar la Historia 1 de forma independiente (quickstart.md § Historia 1)
5. Nota: US1 sola no entrega el valor central del producto (eso es US2) — el "MVP funcional"
   real del negocio requiere US1+US2 juntas; US1 es el MVP técnico mínimo desplegable.

### Incremental Delivery

1. Setup + Foundational → base lista
2. US1 → probar de forma independiente → login funcionando
3. US2 → probar de forma independiente → valor central del producto entregado (Deploy/Demo)
4. US3 → probar de forma independiente → ciclo de stock cerrado
5. US4 → probar de forma independiente → mantenimiento manual del maestro + indicador de alerta
6. US5 → probar de forma independiente → margen de tolerancia configurable
7. Cada historia suma valor sin romper las anteriores

### Parallel Team Strategy

1. El equipo completa Setup + Foundational en conjunto
2. Con Foundational lista:
   - Developer A: US1, luego US2 (comparten el modelo `Producto` que crea US2)
   - Developer B: US4 una vez que T035 (modelo `Producto`) esté mergeado
   - Developer C: US5 una vez que T010 (tabla `ConfiguracionSistema`) esté mergeada
3. US3 conviene abordarla después de US2 por la dependencia real en `OrdenTrabajo` y los
   servicios de matching/stock atómico

---

## Notes

- [P] = archivos distintos, sin dependencias pendientes
- [Story] mapea cada tarea a su historia de usuario para trazabilidad
- Cada historia debe ser completable y testeable de forma independiente
- Verificar que los tests fallan antes de implementar (Principio I, NON-NEGOTIABLE)
- Hacer commit después de cada tarea o grupo lógico
- Detenerse en cada Checkpoint para validar la historia de forma independiente
- Evitar: tareas vagas, conflictos de mismo archivo entre tareas [P], dependencias entre historias
  que rompan su independencia de testeo
- FR-021 aplica a los 4 módulos, pero solo Taller tiene manejo explícito (T060) porque es el
  único módulo con lógica cliente que podría intentar comportarse offline (scanner); los demás
  módulos cumplen FR-021 por diseño, al no implementar ningún caché ni lógica local — un fallo de
  red ahí ya produce el error estándar del interceptor HTTP (T013), sin necesidad de tarea aparte.
