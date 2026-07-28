from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class OrdenTrabajo(Base):
    __tablename__ = "ordenes_trabajo"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    codigo_nest: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    estado: Mapped[str] = mapped_column(
        Enum("vigente", "cerrada", name="estado_orden_trabajo"),
        nullable=False,
        default="vigente",
    )
    multiplicidad: Mapped[int] = mapped_column(Integer, nullable=False)
    espesor_mm: Mapped[float] = mapped_column(Float, nullable=False)
    material: Mapped[str] = mapped_column(String, nullable=False)
    largo_mm: Mapped[float] = mapped_column(Float, nullable=False)
    ancho_mm: Mapped[float] = mapped_column(Float, nullable=False)
    tiempo_ejecucion_estimado: Mapped[str] = mapped_column(String, nullable=False)
    producto_comprometido_id: Mapped[int | None] = mapped_column(
        ForeignKey("productos.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
