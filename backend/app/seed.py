import random
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Producto, Venta


PRODUCTOS_SEED = (
    ("Laptop Pro", "Tecnología", Decimal("1250.00")),
    ("Monitor 27", "Tecnología", Decimal("320.00")),
    ("Silla ergonómica", "Oficina", Decimal("275.00")),
    ("Escritorio", "Oficina", Decimal("410.00")),
    ("Teclado mecánico", "Accesorios", Decimal("95.00")),
)
SEMILLA_VENTAS = 732
CANTIDAD_VENTAS_SEED = 50


def seed_database(session: Session) -> None:
    product_count = session.scalar(select(func.count()).select_from(Producto)) or 0
    sale_count = session.scalar(select(func.count()).select_from(Venta)) or 0
    if product_count or sale_count:
        return

    products = [
        Producto(nombre=nombre, categoria=categoria, precio=precio)
        for nombre, categoria, precio in PRODUCTOS_SEED
    ]
    session.add_all(products)
    session.flush()

    rng = random.Random(SEMILLA_VENTAS)
    start_date = datetime(2025, 1, 1)
    sales = []
    for index in range(CANTIDAD_VENTAS_SEED):
        product = products[rng.randrange(len(products))]
        sales.append(
            Venta(
                producto_id=product.id,
                cantidad=rng.randint(1, 8),
                precio_unitario=product.precio,
                fecha=start_date + timedelta(days=index * 2 + rng.randrange(2)),
            )
        )
    session.add_all(sales)
    session.commit()
