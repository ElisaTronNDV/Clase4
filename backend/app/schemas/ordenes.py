from pydantic import BaseModel, Field


class PiezaSchema(BaseModel):
    descripcion: str
    cantidad: int = Field(gt=0)


class RecorteSchema(BaseModel):
    largo_mm: float | None = None
    ancho_mm: float | None = None


class RecorteCompletoSchema(BaseModel):
    largo_mm: float = Field(gt=0)
    ancho_mm: float = Field(gt=0)


class PropuestaExtraccion(BaseModel):
    multiplicidad: int | None = None
    espesor_mm: float | None = None
    material: str | None = None
    largo_mm: float | None = None
    ancho_mm: float | None = None
    tiempo_ejecucion_estimado: str | None = None
    piezas: list[PiezaSchema] = []
    recortes: list[RecorteSchema] = []
    extraccion_incompleta: bool = False


class OrdenCreate(BaseModel):
    multiplicidad: int = Field(gt=0)
    espesor_mm: float = Field(gt=0)
    material: str = Field(min_length=1)
    largo_mm: float = Field(gt=0)
    ancho_mm: float = Field(gt=0)
    tiempo_ejecucion_estimado: str = Field(min_length=1)
    piezas: list[PiezaSchema] = []
    recortes: list[RecorteCompletoSchema] = []
    confirmar_creacion_automatica: bool = False


class ProductoComprometidoOut(BaseModel):
    id: int
    creado_automaticamente: bool = False


class OrdenOut(BaseModel):
    id: int
    codigo_nest: str
    estado: str
    producto_comprometido: ProductoComprometidoOut
    alerta_stock_bajo: bool


class AdvertenciaProductoInexistente(BaseModel):
    """Cuerpo del 404 cuando no hay producto coincidente y el usuario todavía no
    confirmó el alta automática (FR-015) — el cliente puede reenviar el mismo payload
    con confirmar_creacion_automatica=true."""

    advertencia_producto_inexistente: bool = True
    confirmar_creacion_automatica: bool = False
    mensaje: str = (
        "No existe un producto coincidente en el maestro. Reenviá la confirmación con "
        "confirmar_creacion_automatica=true para darlo de alta con stock físico en 0."
    )
