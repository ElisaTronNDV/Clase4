from sqlalchemy import Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class RecorteDeclarado(Base):
    __tablename__ = "recortes_declarados"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    orden_id: Mapped[int] = mapped_column(ForeignKey("ordenes_trabajo.id"), nullable=False)
    largo_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    ancho_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    producto_resultante_id: Mapped[int | None] = mapped_column(
        ForeignKey("productos.id"), nullable=True
    )
