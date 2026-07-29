from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.producto import Producto
from app.schemas.productos import ProductoCreate, ProductoOut

router = APIRouter(prefix="/api/productos", tags=["productos"])


def _dimensiones_exactas_filtro(datos: ProductoCreate):
    return and_(
        Producto.material == datos.material,
        Producto.espesor_mm == datos.espesor_mm,
        Producto.largo_mm == datos.largo_mm,
        Producto.ancho_mm == datos.ancho_mm,
    )


def _a_producto_out(producto: Producto) -> ProductoOut:
    stock_disponible = producto.stock_fisico - producto.stock_comprometido
    return ProductoOut(
        id=producto.id,
        material=producto.material,
        espesor_mm=producto.espesor_mm,
        largo_mm=producto.largo_mm,
        ancho_mm=producto.ancho_mm,
        stock_fisico=producto.stock_fisico,
        stock_comprometido=producto.stock_comprometido,
        punto_pedido=producto.punto_pedido,
        alerta_stock_bajo=stock_disponible <= producto.punto_pedido,
    )


@router.post("", response_model=ProductoOut, status_code=status.HTTP_201_CREATED)
def crear_producto(
    datos: ProductoCreate,
    usuario=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProductoOut:
    duplicado = db.query(Producto).filter(_dimensiones_exactas_filtro(datos)).first()
    if duplicado is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un producto con exactamente el mismo material, espesor y dimensiones",
        )

    producto = Producto(
        material=datos.material,
        espesor_mm=datos.espesor_mm,
        largo_mm=datos.largo_mm,
        ancho_mm=datos.ancho_mm,
        stock_fisico=datos.stock_fisico,
        stock_comprometido=0,
        punto_pedido=datos.punto_pedido,
    )
    db.add(producto)
    db.commit()
    db.refresh(producto)
    return _a_producto_out(producto)
