from datetime import datetime, timezone

from sqlalchemy import DateTime, Float
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base

MARGEN_TOLERANCIA_DEFAULT_MM = 1.0


class ConfiguracionSistema(Base):
    __tablename__ = "configuracion_sistema"

    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    margen_tolerancia_mm: Mapped[float] = mapped_column(
        Float, nullable=False, default=MARGEN_TOLERANCIA_DEFAULT_MM
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


def seed_configuracion(db) -> None:
    """Crea la fila singleton con el margen por defecto si no existe (FR-029)."""
    existe = db.get(ConfiguracionSistema, 1)
    if existe is None:
        db.add(ConfiguracionSistema(id=1, margen_tolerancia_mm=MARGEN_TOLERANCIA_DEFAULT_MM))
        db.commit()
