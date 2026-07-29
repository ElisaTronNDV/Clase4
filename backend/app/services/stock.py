from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.producto import Producto


def buscar_producto_coincidente(
    db: Session,
    material: str,
    espesor_mm: float,
    largo_mm: float,
    ancho_mm: float,
    margen_tolerancia_mm: float,
) -> Producto | None:
    """Coincidencia por material/espesor exactos y largo/ancho dentro del margen de
    tolerancia, con desempate por menor diferencia total y luego por menor Id
    (research.md §4, FR-031)."""
    diferencia_total = func.abs(Producto.largo_mm - largo_mm) + func.abs(
        Producto.ancho_mm - ancho_mm
    )
    stmt = (
        select(Producto)
        .where(
            Producto.material == material,
            Producto.espesor_mm == espesor_mm,
            func.abs(Producto.largo_mm - largo_mm) <= margen_tolerancia_mm,
            func.abs(Producto.ancho_mm - ancho_mm) <= margen_tolerancia_mm,
        )
        .order_by(diferencia_total.asc(), Producto.id.asc())
        .limit(1)
    )
    return db.execute(stmt).scalars().first()
