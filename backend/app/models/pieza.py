from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Pieza(Base):
    __tablename__ = "piezas"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    orden_id: Mapped[int] = mapped_column(ForeignKey("ordenes_trabajo.id"), nullable=False)
    descripcion: Mapped[str] = mapped_column(String, nullable=False)
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
