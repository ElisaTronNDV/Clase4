# Implementation Plan: Captura de Archivo de Corte y Control de Inventario

**Branch**: `001-captura-corte-inventario` | **Date**: 2026-07-22 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-captura-corte-inventario/spec.md`

## Summary

DyP LaserCore reemplaza la codificación y carga manual del archivo de corte por un flujo asistido:
el usuario sube el PDF del software de la máquina de corte láser, el sistema extrae una **propuesta
editable** de datos (nunca persistida sin confirmación — Principios II/III de la constitución), el
usuario la revisa/corrige, y al confirmar el sistema genera un código NEST, compromete stock del
producto correspondiente e imprime la orden con su código de barras. En Taller, escanear ese código
cierra la orden, descuenta el stock consumido y da de alta o incrementa los recortes sobrantes en
el maestro de inventario. Un módulo de Inventario permite gestión manual de productos, y uno de
Configuración expone el margen de tolerancia dimensional usado para las búsquedas de coincidencia.

Enfoque técnico: aplicación web con backend FastAPI (Python 3.11) + SQLite y frontend Angular
18+/Bootstrap 5, siguiendo el stack ya fijado por `AGENTS.md` y la constitución — este plan no
introduce ninguna tecnología nueva, solo define cómo aplicarla (ver `research.md`).

## Technical Context

**Language/Version**: Python 3.11 (backend) — TypeScript / Angular 18+ (frontend)

**Primary Dependencies**: FastAPI, pdfplumber, python-barcode, passlib[bcrypt], python-jose
(backend) — Angular 18+, Bootstrap 5, ZXing ngx-scanner (frontend)

**Storage**: SQLite, archivo único no versionado (`.gitignore`), creado vacío en el primer arranque

**Testing**: pytest + `TestClient` de FastAPI contra SQLite temporal (backend) — `ng test`
(Jasmine/Karma) (frontend); ver `research.md` §9

**Target Platform**: servidor Linux (backend); navegador de escritorio para Oficina/Inventario/
Configuración y navegador de dispositivo móvil/tablet con cámara para Taller (escaneo)

**Project Type**: aplicación web (backend + frontend separados)

**Performance Goals**: extracción y despliegue de propuesta de PDF en <10 s (SC-002); listados y
búsquedas en <2 s p95 (SC-003)

**Constraints**: sin modo offline en ningún módulo (no solo Taller — ver Clarifications
2026-07-22), requiere conectividad activa (FR-021); sesión JWT expira a las 24 h sin renovación
silenciosa (FR-006), sin bloqueo de cuenta ni rate limiting ante login fallido; margen de
tolerancia leído de configuración en runtime, nunca hardcodeado, solo exige > 0 sin límite
superior (constitución, FR-029); contraseña con mínimo 8 caracteres sin otro requisito de
composición (FR-003); código NEST con formato fijo `NEST-######` (6 dígitos con padding, FR-012);
PDF de carga limitado a 20 MB (FR-007); código de barras CODE_128 verificado por decodificación
independiente antes de servirse, ≥300 DPI, module_width ≥0.3 mm (RNF-06, constitución); creación
automática de producto (FR-015) dentro de la misma transacción atómica que la confirmación de la
orden — si falla, rollback total, nada se persiste

**Scale/Scope**: uso interno de una única empresa (no multi-tenant), cantidad moderada de usuarios
concurrentes entre Oficina y Taller, sin roles ni aislamiento de datos por usuario (FR-004,
Assumptions)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio / regla | Estado | Cómo se cumple |
|---|---|---|
| I. Test-First (NON-NEGOTIABLE) | PASS | `research.md` §9 fija pytest + TestClient (backend, DB real temporal) y `ng test` (frontend) como gate; `/speckit-tasks` deberá generar tareas de test antes de cada tarea de implementación por historia de usuario |
| II. Validación Humana Obligatoria | PASS | `contracts/ordenes.md`: `POST /ordenes/extraer-pdf` nunca persiste, solo `POST /ordenes` (con datos ya revisados) escribe a la base — reflejado también en `data-model.md` (la "propuesta" no es una entidad persistente) |
| III. Extracción como Propuesta | PASS | Mismo mecanismo que el principio II; `research.md` §1 documenta que un fallo/parcialidad de extracción se muestra como campos vacíos editables, nunca como error bloqueante ni como dato ya confirmado |
| IV. Seguridad Mínima No Negociable | PASS | `contracts/auth.md`: passlib[bcrypt] para hash, JWT 24h vía python-jose, todas las rutas no-auth protegidas con 401→redirect; `SECRET_KEY` y secretos solo por variables de entorno (ya fijado en `AGENTS.md`, sin cambios) |
| Restricciones técnicas (tolerancia no hardcodeada) | PASS | `data-model.md` §ConfiguracionSistema + `contracts/configuracion.md`: valor leído de tabla en runtime |
| Restricciones técnicas (código de barras verificado) | PASS | `research.md` §5 + `contracts/ordenes.md` (`GET /ordenes/{id}/codigo-barras`): verificación con pyzbar/zbar antes de servir la imagen |
| Restricciones técnicas (formato explícito del scanner) | PASS | `research.md` §8: `ngx-scanner` configurado con `formats: [CODE_128]` explícito |
| Fuera de alcance (compras, facturación, remitos, roles) | PASS | Ninguno de los contratos ni el data model introduce estas funcionalidades |

No hay violaciones — la sección "Complexity Tracking" no aplica y se omite.

## Project Structure

### Documentation (this feature)

```text
specs/001-captura-corte-inventario/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md         # Phase 1 output (/speckit-plan command)
├── quickstart.md         # Phase 1 output (/speckit-plan command)
├── contracts/            # Phase 1 output (/speckit-plan command)
│   ├── auth.md
│   ├── ordenes.md
│   ├── productos.md
│   └── configuracion.md
├── checklists/
│   ├── requirements.md
│   └── pre-plan.md
└── tasks.md              # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── main.py                # FastAPI app, routers, JWT dependency
│   ├── core/
│   │   ├── config.py           # lee SECRET_KEY y demás desde variables de entorno (RNF-05)
│   │   └── security.py         # hash de password (passlib), emisión/validación JWT (python-jose)
│   ├── db/
│   │   └── session.py          # engine/sesión SQLite
│   ├── models/                 # tablas ORM: usuario, orden_trabajo, pieza, recorte_declarado,
│   │                            #   producto, configuracion_sistema (ver data-model.md)
│   ├── schemas/                # pydantic: request/response por contrato (ver contracts/*.md)
│   ├── services/
│   │   ├── pdf_extraction.py   # pdfplumber, extract_tables + regex acotado (research.md §1-2)
│   │   ├── stock.py            # updates atómicos + matching por tolerancia (research.md §3-4)
│   │   └── barcode.py          # generación CODE_128 + verificación pyzbar (research.md §5)
│   └── api/
│       ├── auth.py              # POST /auth/registro, /auth/login
│       ├── ordenes.py           # extraer-pdf, crear, listar, buscar, cerrar, codigo-barras
│       ├── productos.py         # crear, listar, editar
│       └── configuracion.py     # get, put
└── tests/
    ├── contract/                # un archivo por endpoint de contracts/*.md
    ├── integration/              # flujos completos por historia de usuario (US1..US5)
    └── unit/                     # pdf_extraction, stock (matching/atomicidad), barcode

frontend/
├── src/
│   └── app/
│       ├── auth/                 # login, registro, guard de ruta (FR-002)
│       ├── oficina/              # subir PDF, revisar/editar propuesta, confirmar orden, listado
│       ├── taller/                # escaneo (ngx-scanner CODE_128), búsqueda manual, cierre
│       ├── inventario/            # alta/edición/listado de productos
│       ├── configuracion/         # margen de tolerancia
│       └── shared/                # servicios HTTP, interceptor JWT, modelos TS
└── (tests junto a cada componente/servicio, convención estándar de Angular)
```

**Structure Decision**: aplicación web con backend y frontend separados (Option 2 del template),
ya que el proyecto tiene un backend FastAPI/SQLite independiente y un frontend Angular consumido
vía HTTP — no hay overlap de runtime entre ambos. La estructura de `backend/app/` sigue las capas
ya insinuadas por `AGENTS.md` (modelos, servicios, API) y el frontend sigue la convención estándar
de Angular por feature module, alineada 1:1 con las 5 historias de usuario del spec para que cada
una sea desarrollable/testeable de forma independiente (ver spec §Independent Test de cada
historia).

## Complexity Tracking

*No aplica — el Constitution Check no encontró violaciones que justificar.*
