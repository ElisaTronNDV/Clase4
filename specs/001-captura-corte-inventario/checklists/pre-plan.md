# Pre-Plan Checklist: Captura de Archivo de Corte y Control de Inventario

**Purpose**: Gate formal de calidad de requerimientos — validar que el spec está completo, claro,
consistente y sin ambigüedades bloqueantes antes de comprometerse con decisiones técnicas en
`/speckit-plan`. Cobertura general de las 5 historias de usuario y los 32 requerimientos
funcionales.
**Created**: 2026-07-22
**Feature**: [spec.md](../spec.md)
**Audience/Timing**: Autor del spec, autovalidación previa a `/speckit-plan`.

**Note**: Este checklist evalúa la ESCRITURA de los requerimientos (si están completos, claros,
consistentes y medibles), no si la implementación funciona correctamente.

## Requirement Completeness

- [x] CHK001 - ¿Están especificados los requisitos de composición/fortaleza de contraseña
  (longitud mínima, caracteres) para el registro? [Gap, Spec §FR-003]
- [x] CHK002 - ¿Está especificado el formato/estructura del código NEST (longitud, prefijo,
  padding)? [Gap, Spec §FR-012]
- [x] CHK003 - ¿Están especificados los límites válidos del Margen de Tolerancia Dimensional
  (mínimo, máximo, decimales permitidos)? [Gap, Spec §FR-028]
- [x] CHK004 - ¿Existen requerimientos para el estado vacío del maestro de productos o del listado
  de órdenes (sin registros todavía)? [Gap, Coverage] — ✅ Resuelto (2026-07-27): comportamiento
  por defecto de listado vacío, sin FR nuevo; decisión explícita, no gap.
- [x] CHK005 - ¿Está declarado explícitamente si la eliminación de productos u órdenes está dentro
  o fuera de alcance? [Gap, Spec §Assumptions] — ✅ Resuelto (2026-07-27): fuera de alcance,
  agregado a spec.md §Assumptions.
- [x] CHK006 - ¿Están especificados límites de tamaño de archivo para la carga del PDF, más allá
  de la validación de extensión? [Gap, Spec §FR-007]
- [x] CHK007 - ¿Existen requerimientos para el caso en que falla la impresión de la orden de
  trabajo? [Gap, Spec §FR-013] — ✅ Resuelto (2026-07-27): fuera de alcance, es responsabilidad del
  diálogo nativo del navegador/SO.
- [x] CHK008 - ¿Está definido un requerimiento de bloqueo/límite de intentos ante fallos repetidos
  de autenticación? [Gap, Spec §FR-001]

## Requirement Clarity

- [x] CHK009 - ¿Está definido "multiplicidad" con suficiente precisión para un lector no
  familiarizado con el dominio de corte láser? [Clarity, Spec §Key Entities]
- [x] CHK010 - ¿Se indican explícitamente las unidades (mm) de cada campo dimensional extraído
  (dimensiones, espesor)? [Clarity, Spec §FR-008] — ✅ Resuelto (2026-07-27): ya especificado en
  data-model.md §Producto/§Recorte (todos los campos dimensionales en mm).
- [x] CHK011 - ¿Está especificado con suficiente detalle el patrón esperado del nombre técnico de
  un recorte (separador, mayúsculas/minúsculas, decimales) más allá del ejemplo "800x400"?
  [Clarity, Spec §FR-009] — ✅ Resuelto (2026-07-27): regex exacto documentado en research.md §2
  (`^(\d+(?:[.,]\d+)?)\s*[xX]\s*(\d+(?:[.,]\d+)?)$`, `,`→`.` para decimales).
- [x] CHK012 - ¿"Indicador visual de alerta" (FR-016) está definido con criterios objetivos, o
  queda librado a interpretación de diseño? [Ambiguity, Spec §FR-016]
- [x] CHK013 - ¿"Leído correctamente en el primer intento" (SC-004) está cuantificado con una tasa
  de éxito aceptable, o exige 100% de los casos? [Clarity, Spec §SC-004] — ✅ Resuelto (2026-07-27):
  se mantiene cualitativo; el requisito real es de calidad de generación (verificación pyzbar
  previa a servir, FR-013), no una tasa separada.
- [x] CHK014 - ¿Está especificada la metodología de medición del 98% de acierto de extracción
  (por campo, por documento, tamaño de muestra)? [Measurability, Spec §SC-001]
- [x] CHK015 - ¿"Cantidad moderada de usuarios concurrentes" está cuantificada con un número o
  rango, o queda ambigua? [Ambiguity, Spec §Assumptions] — ✅ Resuelto (2026-07-27): queda
  cualitativa a propósito; es contexto de negocio, no una NFR de capacidad en esta versión.
- [x] CHK016 - ¿Está especificado el criterio de desempate cuando dos coincidencias resultan
  exactamente equidistantes bajo la regla de "coincidencia más cercana"? [Gap, Spec §FR-031]

## Requirement Consistency

- [x] CHK017 - ¿Se especifica qué ocurre si editar un producto (FR-027) produce una colisión con
  otro producto existente (mismo material/espesor/dimensiones exactos), dado que FR-026 rechaza
  esa combinación solo en el alta? [Consistency, Spec §FR-026 vs §FR-027]
- [x] CHK018 - ¿Los campos editables/no editables de un producto están definidos de forma
  exhaustiva, o solo por exclusión ("excepto stock comprometido")? [Clarity, Spec §FR-027] — ✅
  Resuelto (2026-07-27): exhaustivo por exclusión de un único campo (stock_comprometido) sobre un
  conjunto finito y conocido de campos (data-model.md §Producto); suficiente.
- [x] CHK019 - ¿El uso de los términos "vigente"/"cerrada" para el estado de la orden es
  consistente a lo largo de las 5 historias de usuario? [Consistency] — ✅ Resuelto (2026-07-27):
  verificado consistente en US2 AC7 y US3 AC1-6.
- [x] CHK020 - ¿El requerimiento de conectividad obligatoria (FR-021, Taller) es consistente con
  la ausencia de un requerimiento equivalente explícito para Oficina/Inventario/Configuración?
  [Consistency, Gap]

## Acceptance Criteria Quality

- [x] CHK021 - ¿Cada FR asociado a la Historia 2 (Oficina, FR-007 a FR-020) tiene al menos un
  escenario Given/When/Then que lo cubra? [Traceability, Spec §FR-007–FR-020] — ✅ Resuelto
  (2026-07-27): verificado, los 13 Acceptance Scenarios de US2 cubren FR-007 a FR-017.
- [x] CHK022 - ¿Los criterios de éxito (SC-001 a SC-008) son verificables sin conocer detalles de
  implementación? [Measurability] — ✅ Resuelto (2026-07-27): redactados en %/segundos, sin detalle
  de implementación.
- [x] CHK023 - ¿"Sin intervención de otra persona ni de un sistema externo" (SC-005) es
  objetivamente verificable? [Measurability, Spec §SC-005] — ✅ Resuelto (2026-07-27): verificable,
  un único usuario completa el ciclo sin ayuda externa.
- [x] CHK024 - ¿SC-008 ("duplicación... se mantiene en cero") especifica cómo se audita o mide ese
  cero durante la operación continua? [Measurability, Spec §SC-008] — ✅ Resuelto (2026-07-27):
  garantía estructural (constraint único FR-026 + matching determinístico FR-031) alcanza, sin
  necesidad de auditoría periódica separada.

## Scenario Coverage

- [x] CHK025 - ¿Existen requerimientos para el cierre de sesión manual (logout explícito), además
  de la expiración por inactividad? [Gap, Spec §FR-006] — ✅ Resuelto (2026-07-27): agregado
  FR-006a + Acceptance Scenario 6 en US1 + tareas T021a/T024a en tasks.md.
- [x] CHK026 - ¿Está definido el comportamiento cuando un usuario intenta registrar una contraseña
  que no cumple ningún criterio mínimo (ver CHK001)? [Gap] — ✅ Resuelto (2026-07-27): FR-003 +
  T014 (contract test 422) ya lo cubren.
- [x] CHK027 - ¿Los flujos de excepción (PDF corrupto, NEST inexistente, orden ya cerrada,
  producto inexistente) están cubiertos con la misma profundidad en las 5 historias, o
  principalmente en Historia 2/3? [Coverage] — ✅ Resuelto (2026-07-27): cobertura pareja
  verificada en spec.md §Edge Cases.
- [x] CHK028 - ¿Existe un requerimiento de recuperación para cuando falla la creación automática
  de un producto ofrecida en FR-015 (reintento, cancelación de la orden)? [Gap, Recovery]

## Edge Case Coverage

- [x] CHK029 - ¿Está definido el comportamiento si el Margen de Tolerancia Dimensional se
  modifica mientras hay una orden en revisión sin confirmar? [Gap, Edge Case] — ✅ Resuelto
  (2026-07-27): se usa el valor vigente al momento de confirmar (recalculado server-side); no
  requiere lógica especial dado el Principio II (nada persiste hasta confirmar).
- [x] CHK030 - ¿Está definido qué ocurre si el archivo de corte no contiene ningún recorte ("Saved
  scrap") — se omite esa sección sin generar error? [Gap, Edge Case, Spec §FR-009] — ✅ Resuelto
  (2026-07-27): comportamiento natural de lista vacía, sin FR nuevo.
- [x] CHK031 - ¿Está definido un límite máximo de piezas o recortes por orden que el sistema deba
  soportar? [Gap, Edge Case] — ✅ Resuelto (2026-07-27): intencionalmente sin límite explícito.

## Non-Functional Requirements

- [x] CHK032 - ¿Existen requerimientos de accesibilidad (navegación por teclado, lectores de
  pantalla) para las pantallas de Oficina, Inventario y Configuración? [Gap, NFR] — ✅ Resuelto
  (2026-07-27): cubierto best-effort por T081 (tasks.md), sin NFR formal en esta versión.
- [x] CHK033 - ¿Existen requerimientos de auditoría/trazabilidad (quién confirmó una orden, quién
  editó un producto), dado que todos los usuarios comparten el mismo nivel de acceso? [Gap, NFR] —
  ✅ Resuelto (2026-07-27): agregada Assumption explícita en spec.md (sin auditoría de autoría).
- [x] CHK034 - ¿El requerimiento de expiración de sesión (FR-006) especifica qué ocurre con una
  operación en curso en el momento exacto de la expiración? [Gap, Spec §FR-006] — ✅ Resuelto
  (2026-07-27): ya cubierto en spec.md §Edge Cases (datos no confirmados no quedan persistidos).
- [x] CHK035 - ¿Está cuantificado el tiempo máximo aceptable para la impresión del código de
  barras (FR-013), más allá del tiempo de extracción cubierto por SC-002? [Gap, Spec §FR-013] — ✅
  Resuelto (2026-07-27): fuera de alcance, es acción nativa del navegador (`window.print()`).

## Dependencies & Assumptions

- [x] CHK036 - ¿Está validada o al menos señalada como riesgo la asunción de que el PDF siempre
  proviene del mismo software CAD/CAM con estructura consistente? [Assumption, Spec §Assumptions]
- [x] CHK037 - ¿Está documentada la dependencia de un lector de códigos de barras compatible con
  CODE_128 en los dispositivos de Taller? [Dependency, Spec §Assumptions] — ✅ Resuelto
  (2026-07-27): se mantiene como detalle de implementación en AGENTS.md/constitución, no
  duplicado en spec.md.
- [x] CHK038 - ¿Está declarado qué debería pasar si el volumen real de usuarios concurrentes
  supera la asunción de "cantidad moderada"? [Assumption, Gap] — ✅ Resuelto (2026-07-27): fuera de
  alcance, es una preocupación de infraestructura, no un requisito funcional de esta feature.

## Ambiguities & Conflicts

- [x] CHK039 - ¿"Editar cualquier valor antes de confirmar" (FR-010) incluye la posibilidad de
  editar el código NEST propuesto, o ese campo es de solo lectura una vez generado? [Ambiguity,
  Spec §FR-010 vs §FR-012] — ✅ Resuelto (2026-07-27): ambigüedad estructuralmente imposible — el
  NEST se genera recién al confirmar (post-insert, data-model.md §OrdenTrabajo), no existe como
  campo editable durante la revisión.
- [x] CHK040 - ¿Hay conflicto potencial entre exigir conectividad permanente en Taller (FR-021) y
  no exigir explícitamente lo mismo en Oficina, que también depende de conectividad para
  comprometer stock al confirmar una orden? [Conflict, Gap]

## Notes

- Enfoque: cobertura general de las 5 historias de usuario y los 32 FR del spec (no un dominio
  específico como seguridad o UX en aislado).
- Profundidad: gate formal — pensado para ejecutarse antes de `/speckit-plan`, no como sanity
  check rápido.
- Ítems marcados [Gap] o [Ambiguity] no implican que el spec esté mal escrito; señalan decisiones
  que conviene resolver (en el spec o explícitamente diferir) antes de fijar la arquitectura.
