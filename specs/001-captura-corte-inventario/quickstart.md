# Quickstart: Captura de Archivo de Corte y Control de Inventario

Guía de validación manual de punta a punta, una vez implementadas las 5 historias de usuario.
Referencia: `spec.md` (escenarios de aceptación), `contracts/*.md` (formato de cada request).

## Prerrequisitos

Seguir `AGENTS.md` § "Cómo correr" para levantar backend (puerto 8000) y frontend (`ng serve`):

```bash
cp .env.example .env   # SECRET_KEY obligatoria, sin default
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

cd frontend && npm install && ng serve
```

La base SQLite se crea vacía en el primer arranque — no hace falta seed de datos. Un PDF de
ejemplo del archivo de corte está disponible en `Archivos de Corte/` (ver `AGENTS.md`) para validar
Historia 2.

## Validación por historia de usuario

### Historia 1 — Acceso seguro

1. Abrir la app sin sesión iniciada → debe redirigir a `/login` (FR-002, spec §US1-AC2).
2. Registrar un usuario nuevo con password de al menos 8 caracteres (sin otro requisito de
   composición) → cuenta creada (FR-003). Intentar con menos de 8 caracteres → rechazo 422.
3. Intentar registrar el mismo email de nuevo → error, alta rechazada (FR-003).
4. Iniciar sesión con las credenciales creadas → acceso a Oficina, Taller, Inventario y
   Configuración sin restricciones adicionales (FR-004).
5. Intentar login con password incorrecta varias veces seguidas → cada intento responde 401 de
   forma independiente, sin bloqueo de cuenta ni rate limiting (Clarifications 2026-07-22).

**Resultado esperado**: no se puede llegar a ninguna pantalla del sistema sin haber iniciado
sesión primero.

### Historia 2 — Captura de PDF y generación de orden NEST

1. Desde Oficina, subir un PDF de `Archivos de Corte/` → la app muestra multiplicidad (cantidad de
   chapas físicas que consume la orden), dimensiones, espesor, material, tiempo estimado y listado
   de piezas/recortes **sin haberlos guardado todavía** (FR-008 a FR-011). Intentar subir un PDF de
   más de 20 MB → rechazo con error claro (FR-007).
2. Editar manualmente al menos un valor mostrado (ej. corregir una cantidad de pieza) → el valor
   editado es el que se usa al confirmar, no el originalmente extraído (spec §US2-AC6).
3. Confirmar la orden → se genera un código NEST con formato `NEST-######` (ej. `NEST-000001`), la
   orden queda "vigente", y se compromete stock del producto coincidente en una cantidad igual a la
   multiplicidad (FR-012, FR-014). Si no hay producto coincidente, aparece la advertencia y la
   opción de alta automática con stock físico en 0 (FR-015); si esa creación automática falla, la
   confirmación completa de la orden se revierte (nada queda persistido, ver Clarifications
   2026-07-22).
4. Descargar/imprimir el código de barras de la orden y escanearlo con un lector o la cámara del
   celular → debe decodificar el NEST correctamente (FR-013, RNF-06).
5. Desde el listado de órdenes, filtrar por estado "vigente" y buscar por una porción del código
   NEST → debe aparecer solo la orden recién creada (FR-017).
6. Ir a Inventario y verificar que, si el producto comprometido quedó con stock disponible por
   debajo de su punto de pedido, el listado de productos muestra el badge/ícono de alerta junto al
   stock (FR-016) — este indicador solo aparece en Inventario, no en el listado/confirmación de
   órdenes.

**Resultado esperado**: ningún dato del PDF queda en la base sin haber pasado por el paso 2/3 de
revisión y confirmación explícita (Principios II/III de la constitución).

### Historia 3 — Cierre en Taller

1. Con la orden "vigente" de la Historia 2, ir a la pantalla de Taller y escanear su código de
   barras (o ingresar el NEST manualmente) → debe mostrar la orden correcta (FR-018).
2. Finalizar la orden → pasa a "cerrada"; el stock físico y comprometido del producto se descuentan
   según la multiplicidad (FR-019, FR-020).
3. Si la orden tenía recortes declarados: verificar en Inventario que se dieron de alta como
   producto nuevo (si no había coincidencia) o que incrementaron el stock de un producto existente
   dentro del margen de tolerancia (FR-022, FR-023).
4. Intentar cerrar la misma orden de nuevo → debe rechazarse, ya está "cerrada" (spec §Edge Cases).
5. Simular pérdida de conectividad (ej. detener el backend) y repetir el escaneo → debe mostrar un
   error claro, sin permitir operar (FR-021).

**Resultado esperado**: el stock del maestro refleja el consumo real y los recortes ingresados
recién después de este cierre, no antes.

### Historia 4 — Gestión manual del maestro de productos

1. Crear un producto nuevo con todos los campos obligatorios → alta exitosa con Id secuencial
   (FR-024, FR-025).
2. Intentar crear otro producto con exactamente el mismo material/espesor/dimensiones → rechazo
   (FR-026).
3. Editar el punto de pedido de un producto existente → el cambio se refleja en el listado
   (FR-027).
4. Intentar editar las dimensiones de un producto para que coincidan exactamente con otro producto
   existente → rechazo con el mismo criterio que el alta (spec §US4-AC7).
5. Verificar que el campo de stock comprometido no es editable desde este formulario (FR-027).
6. Consultar el listado completo de productos (FR-028).

### Historia 5 — Configuración del margen de tolerancia

1. Entrar a Configuración sin haber tocado nada antes → debe mostrar `1.0 mm` por defecto
   (FR-029).
2. Cambiarlo a otro valor y guardar.
3. Repetir el paso 3 de la Historia 2 (o 3 de la Historia 3) con un producto cuya diferencia de
   dimensiones caiga dentro del nuevo margen pero no del anterior → debe encontrar coincidencia
   usando el valor recién configurado (FR-030).

## Pruebas automatizadas

Antes de considerar cualquier historia "terminada" (Principio I, NON-NEGOTIABLE):

```bash
pytest        # backend — cada FR debe tener al menos un test de contrato/integración
ng test       # frontend
```

La métrica de SC-001 (≥98% de acierto de extracción) se mide **por campo individual** (datos
generales + piezas + recortes), no por documento completo, sobre una muestra de PDFs de
`Archivos de Corte/` (Clarifications 2026-07-22; ver `backend/tests/performance/test_metrics.py`,
T082 de `tasks.md`).

Ver `.specify/memory/constitution.md` § "Flujo de Desarrollo y Calidad" para el criterio de
cobertura por FR.

## Verificación end-to-end ejecutada (T083, 2026-07-29)

Se corrió el flujo completo de las 5 historias contra un backend real (`uvicorn`, DB SQLite
temporal) usando `Archivos de Corte/Ejemplo 1.pdf`, vía llamadas HTTP directas (no a través de la
UI Angular: no hay navegador/Chromium disponible en este entorno de desarrollo, ver nota en
T082). Resultado: todos los pasos de Historia 1 a 5 pasaron, incluyendo:

- Extracción real del PDF (`multiplicidad=1`, `espesor_mm=12.7`, `material=SAE_1010`,
  `largo_mm=1310.0`, `ancho_mm=580.0`, 4 piezas, 0 recortes con dimensiones completas).
- Edición manual de un valor extraído antes de confirmar (spec §US2-AC6).
- Advertencia de producto inexistente + alta automática + `codigo_nest=NEST-000001` (FR-012,
  FR-015).
- Código de barras servido y verificado con pyzbar server-side (FR-013, RNF-06).
- Cierre de la orden en Taller con descuento de stock físico/comprometido (FR-019, FR-020) y
  rechazo del segundo cierre (409).
- Alta manual, edición y listado del maestro de productos (FR-024 a FR-028), incluyendo el
  rechazo por colisión exacta y el bloqueo de `stock_comprometido`.
- Cambio del margen de tolerancia y su efecto inmediato en `buscar_producto_coincidente`
  (FR-029, FR-030), y el 422 ante valor cero.

No se verificó manualmente en este pase: el rechazo de PDF > 20 MB (ya cubierto por
`test_ordenes_extraer_pdf.py`, T026) ni el renderizado real de la UI Angular (labels, badges,
navegación) por la misma limitación de entorno — sí se validó con `ng build` (T081/T082).
Script usado: descartable, no forma parte del repo (`scratchpad/quickstart/run_quickstart.py`).
