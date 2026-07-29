from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from app.core.security import get_current_user
from app.schemas.ordenes import PropuestaExtraccion
from app.services.pdf_extraction import extraer_propuesta

router = APIRouter(prefix="/api/ordenes", tags=["ordenes"])

TAMANO_MAXIMO_BYTES = 20 * 1024 * 1024


@router.post("/extraer-pdf", response_model=PropuestaExtraccion)
async def extraer_pdf(
    archivo: UploadFile,
    usuario=Depends(get_current_user),
) -> PropuestaExtraccion:
    contenido = await archivo.read()
    if len(contenido) > TAMANO_MAXIMO_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="El archivo supera el tamaño máximo permitido de 20 MB",
        )
    if not contenido.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo debe ser un PDF válido",
        )
    propuesta = extraer_propuesta(contenido)
    return PropuestaExtraccion(**propuesta)
