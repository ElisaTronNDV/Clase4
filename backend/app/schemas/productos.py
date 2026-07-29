from pydantic import BaseModel, Field


class ProductoCreate(BaseModel):
    material: str = Field(min_length=1)
    espesor_mm: float = Field(gt=0)
    largo_mm: float = Field(gt=0)
    ancho_mm: float = Field(gt=0)
    stock_fisico: float = Field(ge=0)
    punto_pedido: float = Field(ge=0)


class ProductoUpdate(ProductoCreate):
    pass


class ProductoOut(BaseModel):
    id: int
    material: str
    espesor_mm: float
    largo_mm: float
    ancho_mm: float
    stock_fisico: float
    stock_comprometido: float
    punto_pedido: float
    alerta_stock_bajo: bool

    model_config = {"from_attributes": True}
