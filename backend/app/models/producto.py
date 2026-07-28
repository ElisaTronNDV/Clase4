from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Producto(Base):
    __tablename__ = "productos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    material: Mapped[str] = mapped_column(String, nullable=False)
    espesor_mm: Mapped[float] = mapped_column(Float, nullable=False)
    largo_mm: Mapped[float] = mapped_column(Float, nullable=False)
    ancho_mm: Mapped[float] = mapped_column(Float, nullable=False)
    stock_fisico: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    stock_comprometido: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    punto_pedido: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
