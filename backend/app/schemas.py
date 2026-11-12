from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class RequestSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ProductoCreate(RequestSchema):
    nombre: str = Field(min_length=1, max_length=120)
    categoria: str = Field(min_length=1, max_length=80)
    precio: Decimal = Field(gt=0, max_digits=10, decimal_places=2)


class ProductoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    categoria: str
    precio: Decimal


class VentaCreate(RequestSchema):
    producto_id: int = Field(gt=0)
    cantidad: int = Field(gt=0)
    precio_unitario: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    fecha: datetime | None = None


class VentaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    producto_id: int
    cantidad: int
    precio_unitario: Decimal
    fecha: datetime


class CategoriaIndicadores(BaseModel):
    categoria: str
    ingresos: Decimal
    cantidad_vendida: int
    numero_ventas: int


class IndicadoresRead(BaseModel):
    ingresos_totales: Decimal
    cantidad_vendida: int
    ticket_promedio: Decimal
    numero_ventas: int
    ventas_por_categoria: list[CategoriaIndicadores]


class AgentChatRequest(RequestSchema):
    mensaje: str = Field(min_length=1, max_length=2000)


class AgentChatResponse(BaseModel):
    respuesta: str
    herramientas_usadas: list[str]
