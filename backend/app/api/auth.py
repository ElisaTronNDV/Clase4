from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.usuario import Usuario
from app.schemas.auth import Token, UsuarioCreate, UsuarioLogin, UsuarioOut

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


@router.post("/login", response_model=Token)
def login(credenciales: UsuarioLogin, db: Session = Depends(get_db)) -> Token:
    usuario = db.query(Usuario).filter(Usuario.email == credenciales.email).first()
    if usuario is None or not verify_password(credenciales.password, usuario.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas"
        )
    token, expires_at = create_access_token(subject=usuario.email)
    return Token(access_token=token, expires_at=expires_at)
