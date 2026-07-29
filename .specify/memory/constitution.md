<!--
Sync Impact Report
Version change: [TEMPLATE] → 1.0.0 (initial ratification)
Modified principles: n/a (first concrete version; all placeholders filled)
Added sections:
  - Core Principles I–IV (Test-First, Validación Humana Obligatoria,
    Extracción Automática como Propuesta, Seguridad Mínima No Negociable)
  - Restricciones Técnicas y de Calidad de Datos
  - Flujo de Desarrollo y Calidad
  - Governance
Removed sections: none
Templates requiring updates:
  - .specify/templates/plan-template.md: ✅ no changes needed (Constitution Check
    gate already reads dynamically from this file)
  - .specify/templates/spec-template.md: ✅ no changes needed (requirements/testing
    sections are generic and compatible)
  - .specify/templates/tasks-template.md: ✅ updated — "Tests are OPTIONAL" language
    was contradictory with Principle I (Test-First, NON-NEGOTIABLE) and has been
    changed to mandatory, matching the red-green-refactor workflow
  - .claude/skills/speckit-constitution (this file): n/a, self-referential
Follow-up TODOs: none

---
Version change: 1.0.0 → 1.0.1 (PATCH — aclaración sin cambio de sentido)
Modified principles: n/a
Added sections:
  - Governance: nota de equivalencia de numeración RF-XX/RNF-XX (PRD) ↔ FR-XXX/SC-XXX
    (spec.md), para trazabilidad entre esta constitución y specs/001-captura-corte-inventario/.
    Originado en /speckit-analyze (hallazgo I1) al cerrar la feature 001.
Removed sections: none
Templates requiring updates: ninguna (no cambia ningún principio ni gate)
Follow-up TODOs: none
-->

# DyP LaserCore Constitution

## Core Principles

### I. Test-First (NON-NEGOTIABLE)

Los tests se escriben antes que la implementación, para toda funcionalidad nueva y
todo bug fix. El ciclo Red-Green-Refactor es obligatorio: (1) escribir un test que
falle, (2) escribir el código mínimo para que pase, (3) refactorizar manteniendo los
tests en verde. Un PR que agrega comportamiento sin un test previo que lo cubra no
es aceptable, aunque el código "funcione". pytest (backend) y ng test (frontend) son
el gate de calidad; ninguna funcionalidad se considera terminada sin sus tests
pasando.

**Rationale**: en un sistema que mueve stock e inventario real, el costo de un
regresión no detectada es alto (stock incorrecto, duplicados, órdenes mal
generadas). TDD fuerza a especificar el comportamiento esperado antes de
construirlo y deja una red de regresión permanente.

### II. Validación Humana Obligatoria Antes de Persistir

Ninguna orden de trabajo ni dato derivado del archivo de corte (PDF) se guarda en
la base de datos sin que el usuario lo haya revisado y, si corresponde, editado y
confirmado explícitamente. Esto aplica en particular a la captura y extracción de
datos generales, piezas y recortes (RF-01/RF-02/RF-02-a), y a cualquier flujo futuro
que derive datos de negocio de una fuente automatizada. No existe un modo
"auto-confirmar" ni una vía que persista datos extraídos sin paso por esta
revisión.

**Rationale**: mitigación directa del riesgo "Captura de datos erróneos" señalado
en el PRD; el proceso reemplaza captura manual pero no elimina la responsabilidad
humana sobre la exactitud del dato antes de comprometer stock.

### III. La Extracción Automática es una Propuesta, no una Fuente de Verdad

El resultado de pdfplumber (o cualquier extractor automático que se incorpore) es
siempre una PROPUESTA editable en pantalla, nunca un hecho consumado ni una
escritura directa a la base de datos. El sistema no debe tratar ese resultado como
dato validado de negocio hasta que pase por el gate de la Principio II. El objetivo
de acierto de extracción (RNF-01: >98%) es una meta de calidad de la propuesta, no
una justificación para saltear o debilitar la revisión humana, ni siquiera en el
caso de alta confianza de match.

**Rationale**: separa con claridad "dato sugerido por software" de "dato de negocio
confiable", evitando que un fallo silencioso de extracción (formato de PDF distinto,
campo mal parseado) contamine el maestro de productos o el stock comprometido.

### IV. Seguridad Mínima No Negociable

La ausencia de roles y permisos diferenciados (RF-19-a) no exime de seguridad
básica; son mínimos innegociables:

- Contraseñas: hash con bcrypt/argon2 vía passlib, nunca texto plano (RNF-04).
- Sesión: JWT con expiración de 24 h (RNF-05); toda ruta de la aplicación exige
  autenticación previa, y un usuario no autenticado se redirige al login (RF-18-a).
- Secretos y claves (SECRET_KEY, API keys) se leen únicamente desde variables de
  entorno; nunca se hardcodean ni se versionan en el repositorio.

**Rationale**: "sin roles" significa que todo usuario autenticado tiene el mismo
acceso, no que el perímetro de autenticación deje de ser el único control de
acceso al sistema — degradarlo expone todo el inventario y las órdenes de trabajo
por igual.

## Restricciones Técnicas y de Calidad de Datos

- Stack de referencia: Python 3.11, FastAPI, SQLite, Angular 18+, Bootstrap 5,
  pdfplumber, python-barcode, ZXing ngx-scanner, passlib[bcrypt], python-jose.
  Cambiar una pieza de este stack requiere enmendar esta constitución o justificar
  la excepción en el plan de la feature.
- El margen de tolerancia dimensional (RF-17) DEBE leerse de configuración en
  tiempo de ejecución (default 1.0 mm); está prohibido hardcodearlo en el código.
- Todo código de barras generado DEBE verificarse con un lector independiente
  (ej. zbar/pyzbar) a resolución de impresión típica (≥300 DPI por RNF-06), no solo
  validarse visualmente como imagen en pantalla. El ancho de barra mínimo
  (module_width / X-dimension) no debe ser inferior a 0.3 mm, y el
  ancho/alto de imagen debe respetar la relación de aspecto real.
- Los componentes de escaneo (ZXing/ngx-scanner) DEBEN configurar explícitamente
  el formato esperado (CODE_128 para códigos NEST); no depender del default de la
  librería, que típicamente solo soporta QR.
- Fuera de alcance (no implementar sin enmienda previa): órdenes de compra,
  facturación, generación de remitos, roles/permisos diferenciados, aislamiento de
  datos por usuario.

## Flujo de Desarrollo y Calidad

- Ciclo Red-Green-Refactor obligatorio (ver Principio I): un PR debe poder mostrar
  que el test correspondiente falló antes de la implementación.
- Los criterios de aceptación (AC-XX) del PRD son la base para los tests de
  contrato/integración de cada requerimiento funcional (RF-XX); un RF sin AC
  cubierto por al menos un test no se considera implementado.
- pytest (backend) y ng test (frontend) son el gate de CI; ninguna feature se
  mergea con tests en rojo o sin tests para el comportamiento que introduce.

## Governance

- Esta constitución prevalece sobre cualquier práctica o preferencia individual de
  implementación; en caso de conflicto, la constitución gana.
- Toda enmienda requiere: (1) registrar el cambio en un Sync Impact Report al
  inicio del archivo, (2) revisar y actualizar las plantillas dependientes
  (`plan-template.md`, `spec-template.md`, `tasks-template.md`) si corresponde,
  (3) incrementar la versión según semver (MAJOR: eliminación o redefinición
  incompatible de un principio; MINOR: principio o sección nueva; PATCH:
  aclaración o corrección de redacción sin cambio de sentido).
- Todo PR o review debe verificar cumplimiento de los cuatro principios; una
  violación debe justificarse explícitamente en "Complexity Tracking" del plan
  correspondiente, o el PR se rechaza.
- `AGENTS.md` (y `CLAUDE.md`, que lo referencia) es la guía operativa de runtime
  (comandos, stack, "qué no hacer") y debe mantenerse consistente con esta
  constitución; en caso de discrepancia, esta constitución es la fuente de verdad.
- Los principios de esta constitución usan la numeración `RF-XX`/`RNF-XX` heredada
  del PRD original (PRD-001). El spec derivado
  (`specs/001-captura-corte-inventario/spec.md`) renumeró los mismos requisitos como
  `FR-XXX`/`SC-XXX`; ambas numeraciones coexisten y refieren al mismo requisito de
  negocio — ver `specs/001-captura-corte-inventario/fr-test-map.md` para la
  trazabilidad FR→test vigente.

**Version**: 1.0.1 | **Ratified**: 2026-07-21 | **Last Amended**: 2026-07-29
