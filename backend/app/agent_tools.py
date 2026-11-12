from decimal import Decimal, ROUND_HALF_UP

from pydantic import BaseModel, ConfigDict, Field, ValidationError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Producto, Venta


CENTAVOS = Decimal("0.01")


class ToolArguments(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ProductArguments(ToolArguments):
    producto: str = Field(min_length=1, max_length=120)


class CategoryArguments(ToolArguments):
    categoria: str = Field(min_length=1, max_length=80)


def _money(value: Decimal | float | int | None) -> str:
    return str(Decimal(str(value or 0)).quantize(CENTAVOS, rounding=ROUND_HALF_UP))


def _validated_arguments(model: type[ToolArguments], arguments: dict[str, object]) -> dict[str, object]:
    try:
        return model.model_validate(arguments).model_dump()
    except ValidationError:
        return {"error": "Argumentos inválidos. Proporciona un nombre válido para el filtro solicitado."}


def consultar_resumen_ventas(session: Session, arguments: dict[str, object]) -> dict[str, object]:
    if arguments:
        return {"error": "Esta herramienta no acepta argumentos."}

    totals = session.execute(
        select(
            func.coalesce(func.sum(Venta.cantidad * Venta.precio_unitario), 0),
            func.coalesce(func.sum(Venta.cantidad), 0),
            func.count(Venta.id),
        )
    ).one()
    income = Decimal(str(totals[0] or 0)).quantize(CENTAVOS, rounding=ROUND_HALF_UP)
    units = int(totals[1])
    orders = int(totals[2])
    average_ticket = (income / orders).quantize(CENTAVOS, rounding=ROUND_HALF_UP) if orders else Decimal("0.00")

    category_rows = session.execute(
        select(
            Producto.categoria,
            func.sum(Venta.cantidad * Venta.precio_unitario),
            func.sum(Venta.cantidad),
            func.count(Venta.id),
        )
        .join(Venta, Venta.producto_id == Producto.id)
        .group_by(Producto.categoria)
        .order_by(Producto.categoria)
    )
    categories = [
        {
            "categoria": category,
            "ingresos": _money(category_income),
            "unidades_vendidas": int(category_units),
            "numero_ventas": int(category_orders),
        }
        for category, category_income, category_units, category_orders in category_rows
    ]
    return {
        "ingresos_totales": _money(income),
        "unidades_vendidas": units,
        "numero_ventas": orders,
        "ticket_promedio": _money(average_ticket),
        "ventas_por_categoria": categories,
    }


def consultar_ventas_por_producto(session: Session, arguments: dict[str, object]) -> dict[str, object]:
    parsed = _validated_arguments(ProductArguments, arguments)
    if "error" in parsed:
        return parsed

    rows = session.execute(
        select(
            Producto.id,
            Producto.nombre,
            Producto.categoria,
            Producto.precio,
            func.coalesce(func.sum(Venta.cantidad), 0),
            func.coalesce(func.sum(Venta.cantidad * Venta.precio_unitario), 0),
            func.count(Venta.id),
        )
        .outerjoin(Venta, Venta.producto_id == Producto.id)
        .where(func.lower(Producto.nombre) == parsed["producto"].lower())
        .group_by(Producto.id)
        .order_by(Producto.id)
    )
    results = [
        {
            "producto_id": product_id,
            "producto": name,
            "categoria": category,
            "precio_actual": _money(price),
            "unidades_vendidas": int(units),
            "ingresos": _money(income),
            "numero_ventas": int(orders),
        }
        for product_id, name, category, price, units, income, orders in rows
    ]
    return {"producto_buscado": parsed["producto"], "resultados": results}


def consultar_ventas_por_categoria(session: Session, arguments: dict[str, object]) -> dict[str, object]:
    parsed = _validated_arguments(CategoryArguments, arguments)
    if "error" in parsed:
        return parsed

    rows = session.execute(
        select(
            Producto.categoria,
            func.coalesce(func.sum(Venta.cantidad), 0),
            func.coalesce(func.sum(Venta.cantidad * Venta.precio_unitario), 0),
            func.count(Venta.id),
        )
        .outerjoin(Venta, Venta.producto_id == Producto.id)
        .where(func.lower(Producto.categoria) == parsed["categoria"].lower())
        .group_by(Producto.categoria)
        .order_by(Producto.categoria)
    )
    results = [
        {
            "categoria": category,
            "unidades_vendidas": int(units),
            "ingresos": _money(income),
            "numero_ventas": int(orders),
        }
        for category, units, income, orders in rows
    ]
    return {"categoria_buscada": parsed["categoria"], "resultados": results}


TOOL_HANDLERS = {
    "consultar_resumen_ventas": consultar_resumen_ventas,
    "consultar_ventas_por_producto": consultar_ventas_por_producto,
    "consultar_ventas_por_categoria": consultar_ventas_por_categoria,
}
