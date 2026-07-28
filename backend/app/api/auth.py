from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.session import get_db
from app.models.usuario import Usuario
from app.schemas.auth import UsuarioCreate, UsuarioOut

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/registro", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
def registro(datos: UsuarioCreate, db: Session = Depends(get_db)) -> Usuario:
    existente = db.query(Usuario).filter(Usuario.email == datos.email).first()
    if existente is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="El email ya está registrado"
        )
    usuario = Usuario(email=datos.email, password_hash=hash_password(datos.password))
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario
