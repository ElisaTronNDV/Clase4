from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.configuracion_sistema import MARGEN_TOLERANCIA_DEFAULT_MM, ConfiguracionSistema
from app.schemas.configuracion import ConfiguracionOut, ConfiguracionUpdate

router = APIRouter(prefix="/api/configuracion", tags=["configuracion"])


@router.get("", response_model=ConfiguracionOut)
def obtener_configuracion(
    usuario=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConfiguracionOut:
    configuracion = db.get(ConfiguracionSistema, 1)
    margen = configuracion.margen_tolerancia_mm if configuracion else MARGEN_TOLERANCIA_DEFAULT_MM
    return ConfiguracionOut(margen_tolerancia_mm=margen)


@router.put("", response_model=ConfiguracionOut)
def actualizar_configuracion(
    datos: ConfiguracionUpdate,
    usuario=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConfiguracionOut:
    configuracion = db.get(ConfiguracionSistema, 1)
    if configuracion is None:
        configuracion = ConfiguracionSistema(id=1)
        db.add(configuracion)
    configuracion.margen_tolerancia_mm = datos.margen_tolerancia_mm
    db.commit()
    db.refresh(configuracion)
    return ConfiguracionOut(margen_tolerancia_mm=configuracion.margen_tolerancia_mm)
