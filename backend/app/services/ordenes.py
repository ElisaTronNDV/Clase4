def generar_codigo_nest(id_fila: int) -> str:
    """Formatea el codigo_nest a partir del id autoincremental de la fila recién
    insertada de OrdenTrabajo, sin consulta previa separada que pueda
    desincronizarse bajo escritura concurrente (research.md §10, FR-012)."""
    return f"NEST-{id_fila:06d}"
