# Contract: Configuración del Sistema (Historia 5)

Todas las rutas requieren autenticación. Cubre FR-029, FR-030.

## GET /api/configuracion

**Response 200**:
```json
{ "margen_tolerancia_mm": 1.0 }
```

Devuelve el valor por defecto (`1.0`) si nunca fue modificado (FR-029).

## PUT /api/configuracion

**Request**:
```json
{ "margen_tolerancia_mm": 1.5 }
```

**Response 200**: valor actualizado. A partir de esta respuesta, toda búsqueda de coincidencia de
producto (Oficina/Taller, `contracts/ordenes.md`) usa este nuevo valor (FR-030).

**Response 422**: valor no positivo (cero o negativo) o con formato inválido; no hay límite
superior explícito (ver Clarifications 2026-07-22 en `spec.md`, `data-model.md`
§ConfiguracionSistema).
