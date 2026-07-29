# Mapa FR → Test

Referencia rápida de qué test cubre cada requisito funcional (FR-001..FR-032, incluidas las
clarificaciones de las sesiones 2026-07-21 y 2026-07-22). Constitución § Flujo de Desarrollo y
Calidad exige que todo FR tenga al menos un test automatizado que lo verifique; FR-021 es la única
excepción documentada (ver nota al final).

| FR | Descripción breve | Test(s) |
|----|--------------------|---------|
| FR-001 | Pantalla de login (email/password) | `backend/tests/contract/test_auth_login.py`, `backend/tests/integration/test_auth_flow.py` |
| FR-002 | Redirección a `/login` sin sesión válida | `backend/tests/integration/test_auth_flow.py` (401 backend), `frontend/src/app/auth/auth.guard.spec.ts` |
| FR-003 | Autorregistro, password `min_length=8` sin otra composición | `backend/tests/contract/test_auth_registro.py` |
| FR-004 | Mismo nivel de acceso para todo usuario autenticado (sin roles) | `backend/tests/integration/test_auth_flow.py` |
| FR-005 | Hash seguro de password + emisión de JWT | `backend/tests/contract/test_auth_login.py`, `backend/tests/contract/test_auth_registro.py` |
| FR-006 | Expiración de sesión a las 24 h (`exp` del JWT) | `backend/tests/contract/test_auth_login.py` |
| FR-006a | Cerrar sesión explícitamente | `frontend/src/app/auth/logout/logout.component.spec.ts` |
| FR-007 | Subir PDF, tamaño máximo 20 MB (413) | `backend/tests/contract/test_ordenes_extraer_pdf.py` |
| FR-008 | Extracción de datos generales del PDF | `backend/tests/unit/test_pdf_extraction.py` |
| FR-009 | Extracción de dimensiones de piezas/recortes | `backend/tests/unit/test_pdf_extraction.py` |
| FR-010 | Presentar datos extraídos como propuesta editable | `backend/tests/contract/test_ordenes_extraer_pdf.py` |
| FR-011 | No persistir nada hasta confirmar (SC-006) | `backend/tests/contract/test_ordenes_extraer_pdf.py` |
| FR-012 | Código NEST único, formato `NEST-######` | `backend/tests/unit/test_nest_generation.py`, `backend/tests/contract/test_ordenes_crear.py` |
| FR-013 | Documento imprimible con código de barras verificado | `backend/tests/contract/test_ordenes_codigo_barras.py` |
| FR-014 | Compromiso de stock == multiplicidad al confirmar | `backend/tests/contract/test_ordenes_crear.py` |
| FR-015 | Advertencia + alta automática de producto inexistente, con rollback total si falla | `backend/tests/contract/test_ordenes_crear.py` |
| FR-016 | Indicador visual de alerta de stock bajo | `backend/tests/contract/test_productos_listar.py` |
| FR-017 | Listar órdenes filtrando por estado y/o NEST parcial (combinable) | `backend/tests/contract/test_ordenes_listar.py` |
| FR-018 | Localizar orden por escaneo o NEST manual | `backend/tests/contract/test_ordenes_buscar.py` |
| FR-019 | Finalizar una orden "vigente" | `backend/tests/contract/test_ordenes_cerrar.py` |
| FR-020 | Descuento de stock físico y comprometido al finalizar | `backend/tests/contract/test_ordenes_cerrar.py`, `backend/tests/unit/test_stock_atomic.py` |
| FR-021 | Requiere conectividad activa, sin caché/reintento automático | Sin test automatizado — ver nota |
| FR-022 | Alta de recorte como nuevo producto si no hay coincidencia | `backend/tests/contract/test_ordenes_cerrar.py` |
| FR-023 | Incremento de stock del producto existente si hay coincidencia | `backend/tests/contract/test_ordenes_cerrar.py` |
| FR-024 | Alta manual de producto en el maestro | `backend/tests/contract/test_productos_crear.py` |
| FR-025 | Id único y secuencial asignado automáticamente | `backend/tests/contract/test_productos_crear.py` |
| FR-026 | Rechazo de alta duplicada exacta (409) | `backend/tests/contract/test_productos_crear.py` |
| FR-027 | Edición de producto, `stock_comprometido` no editable | `backend/tests/contract/test_productos_editar.py` |
| FR-028 | Listado completo del maestro de productos | `backend/tests/contract/test_productos_listar.py` |
| FR-029 | Apartado de configuración del margen de tolerancia (default 1.0) | `backend/tests/contract/test_configuracion_get.py`, `backend/tests/contract/test_configuracion_put.py` |
| FR-030 | El margen vigente afecta las búsquedas de coincidencia (Oficina/Taller) | `backend/tests/contract/test_configuracion_put.py` |
| FR-031 | Desempate por menor Id en empate exacto de tolerancia | `backend/tests/unit/test_stock_matching.py` |
| FR-032 | Actualización atómica de stock ante deltas concurrentes | `backend/tests/unit/test_stock_atomic.py` |

## Integration tests (flujo completo por historia)

- `backend/tests/integration/test_auth_flow.py` — Historia 1 (FR-001, FR-002, FR-004)
- `backend/tests/integration/test_oficina_flow.py` — Historia 2 (FR-007 a FR-017)
- `backend/tests/integration/test_taller_flow.py` — Historia 3 (FR-018 a FR-023)

## Nota sobre FR-021

FR-021 aplica a los 4 módulos, pero solo Taller tiene manejo explícito en código
(`cerrar-orden.component.ts`) porque es el único módulo con lógica cliente que podría intentar
comportarse offline (scanner). Los demás módulos cumplen FR-021 por diseño, al no implementar
ningún caché ni lógica local — un fallo de red ya produce el error estándar del interceptor HTTP
(`auth.interceptor.ts`), sin necesidad de test dedicado. La verificación manual de este
comportamiento forma parte de `quickstart.md` (T083).
