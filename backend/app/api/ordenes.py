from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.configuracion_sistema import MARGEN_TOLERANCIA_DEFAULT_MM, ConfiguracionSistema
from app.models.orden_trabajo import OrdenTrabajo
from app.models.pieza import Pieza
from app.models.producto import Producto
from app.models.recorte_declarado import RecorteDeclarado
from app.schemas.ordenes import (
    AdvertenciaProductoInexistente,
    OrdenCreate,
    OrdenDetalleOut,
    OrdenListadoOut,
    OrdenOut,
    PiezaSchema,
    ProductoComprometidoOut,
    PropuestaExtraccion,
    RecorteSchema,
)
from app.services.barcode import GeneracionCodigoBarrasError, generar_codigo_barras_png
from app.services.ordenes import generar_codigo_nest
from app.services.pdf_extraction import extraer_propuesta
from app.services.stock import aplicar_delta_stock, buscar_producto_coincidente

router = APIRouter(prefix="/api/ordenes", tags=["ordenes"])

TAMANO_MAXIMO_BYTES = 20 * 1024 * 1024


def _obtener_margen_tolerancia_mm(db: Session) -> float:
    configuracion = db.get(ConfiguracionSistema, 1)
    return configuracion.margen_tolerancia_mm if configuracion else MARGEN_TOLERANCIA_DEFAULT_MM


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


@router.post("", response_model=OrdenOut, status_code=status.HTTP_201_CREATED)
def crear_orden(
    datos: OrdenCreate,
    usuario=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OrdenOut:
    margen_tolerancia_mm = _obtener_margen_tolerancia_mm(db)
    producto = buscar_producto_coincidente(
        db,
        material=datos.material,
        espesor_mm=datos.espesor_mm,
        largo_mm=datos.largo_mm,
        ancho_mm=datos.ancho_mm,
        margen_tolerancia_mm=margen_tolerancia_mm,
    )

    if producto is None and not datos.confirmar_creacion_automatica:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=AdvertenciaProductoInexistente().model_dump(),
        )

    creado_automaticamente = False

    try:
        if producto is None:
            producto = Producto(
                material=datos.material,
                espesor_mm=datos.espesor_mm,
                largo_mm=datos.largo_mm,
                ancho_mm=datos.ancho_mm,
                stock_fisico=0,
                stock_comprometido=0,
                punto_pedido=0,
            )
            db.add(producto)
            db.flush()
            creado_automaticamente = True

        orden = OrdenTrabajo(
            codigo_nest="",
            estado="vigente",
            multiplicidad=datos.multiplicidad,
            espesor_mm=datos.espesor_mm,
            material=datos.material,
            largo_mm=datos.largo_mm,
            ancho_mm=datos.ancho_mm,
            tiempo_ejecucion_estimado=datos.tiempo_ejecucion_estimado,
            producto_comprometido_id=producto.id,
        )
        db.add(orden)
        db.flush()
        orden.codigo_nest = generar_codigo_nest(orden.id)

        for pieza in datos.piezas:
            db.add(
                Pieza(orden_id=orden.id, descripcion=pieza.descripcion, cantidad=pieza.cantidad)
            )
        for recorte in datos.recortes:
            db.add(
                RecorteDeclarado(
                    orden_id=orden.id, largo_mm=recorte.largo_mm, ancho_mm=recorte.ancho_mm
                )
            )

        aplicar_delta_stock(db, producto.id, "stock_comprometido", float(datos.multiplicidad))
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudo confirmar la orden: la operación se revirtió por completo",
        ) from exc

    db.refresh(producto)
    stock_disponible = producto.stock_fisico - producto.stock_comprometido
    alerta_stock_bajo = stock_disponible <= producto.punto_pedido

    return OrdenOut(
        id=orden.id,
        codigo_nest=orden.codigo_nest,
        estado=orden.estado,
        producto_comprometido=ProductoComprometidoOut(
            id=producto.id, creado_automaticamente=creado_automaticamente
        ),
        alerta_stock_bajo=alerta_stock_bajo,
    )


@router.get("", response_model=list[OrdenListadoOut])
def listar_ordenes(
    estado: str | None = None,
    nest: str | None = None,
    usuario=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[OrdenTrabajo]:
    query = db.query(OrdenTrabajo)
    if estado:
        query = query.filter(OrdenTrabajo.estado == estado)
    if nest:
        query = query.filter(OrdenTrabajo.codigo_nest.contains(nest))
    return query.order_by(OrdenTrabajo.id).all()


@router.get("/buscar", response_model=OrdenDetalleOut)
def buscar_orden(
    codigo_nest: str,
    usuario=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OrdenDetalleOut:
    orden = db.query(OrdenTrabajo).filter(OrdenTrabajo.codigo_nest == codigo_nest).first()
    if orden is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Orden inexistente")

    piezas = db.query(Pieza).filter(Pieza.orden_id == orden.id).all()
    recortes = db.query(RecorteDeclarado).filter(RecorteDeclarado.orden_id == orden.id).all()

    return OrdenDetalleOut(
        id=orden.id,
        codigo_nest=orden.codigo_nest,
        estado=orden.estado,
        material=orden.material,
        espesor_mm=orden.espesor_mm,
        largo_mm=orden.largo_mm,
        ancho_mm=orden.ancho_mm,
        multiplicidad=orden.multiplicidad,
        tiempo_ejecucion_estimado=orden.tiempo_ejecucion_estimado,
        created_at=orden.created_at,
        closed_at=orden.closed_at,
        piezas=[PiezaSchema(descripcion=p.descripcion, cantidad=p.cantidad) for p in piezas],
        recortes=[RecorteSchema(largo_mm=r.largo_mm, ancho_mm=r.ancho_mm) for r in recortes],
    )


@router.get("/{id_orden}/codigo-barras")
def codigo_barras(
    id_orden: int,
    usuario=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    orden = db.get(OrdenTrabajo, id_orden)
    if orden is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Orden inexistente")

    try:
        imagen_png = generar_codigo_barras_png(orden.codigo_nest)
    except GeneracionCodigoBarrasError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudo generar un código de barras verificable",
        ) from exc

    return Response(content=imagen_png, media_type="image/png")
