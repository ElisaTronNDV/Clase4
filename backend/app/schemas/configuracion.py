from pydantic import BaseModel, Field


class ConfiguracionOut(BaseModel):
    margen_tolerancia_mm: float

    model_config = {"from_attributes": True}


class ConfiguracionUpdate(BaseModel):
    margen_tolerancia_mm: float = Field(gt=0)
