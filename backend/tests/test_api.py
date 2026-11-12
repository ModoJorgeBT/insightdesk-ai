from decimal import Decimal

from sqlalchemy import func, select

from app.main import create_app
from app.models import Producto, Venta
from app.seed import CANTIDAD_VENTAS_SEED
from tests.conftest import ASGIClient, run_lifespan


def test_seed_creates_50_reproducible_sales_and_is_idempotent(api) -> None:
    session_factory = api.app.state.session_factory
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(Venta)) == CANTIDAD_VENTAS_SEED
        assert session.scalar(select(func.count()).select_from(Producto)) == 5
        first_seed = list(
            session.execute(
                select(Venta.producto_id, Venta.cantidad, Venta.precio_unitario, Venta.fecha)
                .order_by(Venta.id)
            )
        )

    run_lifespan(api.app)
    with session_factory() as session:
        second_seed = list(
            session.execute(
                select(Venta.producto_id, Venta.cantidad, Venta.precio_unitario, Venta.fecha)
                .order_by(Venta.id)
            )
        )
        assert second_seed == first_seed
        assert session.scalar(select(func.count()).select_from(Venta)) == CANTIDAD_VENTAS_SEED


def test_seeded_data_persists_after_app_restart(api) -> None:
    database_url = str(api.app.state.engine.url)
    restarted_app = create_app(database_url)
    lifecycle_messages = run_lifespan(restarted_app)
    assert lifecycle_messages[0]["type"] == "lifespan.startup.complete"

    restarted_client = ASGIClient(restarted_app)
    product_status, products = restarted_client.request("GET", "/api/productos")
    sale_status, sales = restarted_client.request("GET", "/api/ventas")

    assert product_status == 200
    assert len(products) == 5
    assert sale_status == 200
    assert len(sales) == CANTIDAD_VENTAS_SEED
    restarted_app.state.engine.dispose()


def test_product_and_sales_endpoints_validate_and_persist(api) -> None:
    status_code, product = api.request(
        "POST",
        "/api/productos",
        {"nombre": "Producto de prueba", "categoria": "Pruebas", "precio": "12.50"},
    )
    assert status_code == 201
    assert product["nombre"] == "Producto de prueba"
    assert product["precio"] == "12.50"

    status_code, invalid_product = api.request(
        "POST",
        "/api/productos",
        {"nombre": " ", "categoria": "Pruebas", "precio": "0", "otro": "no permitido"},
    )
    assert status_code == 422
    assert invalid_product["detail"]

    status_code, sale = api.request(
        "POST",
        "/api/ventas",
        {
            "producto_id": product["id"],
            "cantidad": 3,
            "precio_unitario": "11.25",
            "fecha": "2026-01-15T12:00:00",
        },
    )
    assert status_code == 201
    assert sale["cantidad"] == 3

    status_code, missing_product_sale = api.request(
        "POST",
        "/api/ventas",
        {"producto_id": 9999, "cantidad": 1, "precio_unitario": "1.00"},
    )
    assert status_code == 404
    assert missing_product_sale["detail"] == "El producto indicado no existe"

    status_code, products = api.request("GET", "/api/productos")
    assert status_code == 200
    assert any(item["id"] == product["id"] for item in products)

    status_code, sales = api.request("GET", "/api/ventas")
    assert status_code == 200
    assert any(item["id"] == sale["id"] for item in sales)

    status_code, indicators = api.request("GET", "/api/indicadores")
    assert status_code == 200
    assert indicators["cantidad_vendida"] >= 3
    assert any(item["categoria"] == "Pruebas" for item in indicators["ventas_por_categoria"])


def test_seed_indicators_match_the_seeded_sales(api) -> None:
    status_code, indicators = api.request("GET", "/api/indicadores")

    assert status_code == 200
    assert indicators["numero_ventas"] == CANTIDAD_VENTAS_SEED
    assert indicators["cantidad_vendida"] == 225
    assert Decimal(indicators["ingresos_totales"]) == Decimal("114825.00")
    assert Decimal(indicators["ticket_promedio"]) == Decimal("2296.50")
    assert indicators["ventas_por_categoria"] == [
        {
            "categoria": "Accesorios",
            "ingresos": "1615.00",
            "cantidad_vendida": 17,
            "numero_ventas": 4,
        },
        {
            "categoria": "Oficina",
            "ingresos": "35640.00",
            "cantidad_vendida": 108,
            "numero_ventas": 23,
        },
        {
            "categoria": "Tecnología",
            "ingresos": "77570.00",
            "cantidad_vendida": 100,
            "numero_ventas": 23,
        },
    ]
    assert sum(item["numero_ventas"] for item in indicators["ventas_por_categoria"]) == 50
    assert sum(item["cantidad_vendida"] for item in indicators["ventas_por_categoria"]) == indicators[
        "cantidad_vendida"
    ]
    assert sum(Decimal(item["ingresos"]) for item in indicators["ventas_por_categoria"]) == Decimal(
        indicators["ingresos_totales"]
    )


def test_indicators_are_zero_when_seed_is_disabled(tmp_path) -> None:
    app = create_app(
        f"sqlite:///{(tmp_path / 'empty.db').as_posix()}",
        seed_on_startup=False,
    )
    run_lifespan(app)
    status_code, indicators = ASGIClient(app).request("GET", "/api/indicadores")

    assert status_code == 200
    assert indicators == {
        "ingresos_totales": "0.00",
        "cantidad_vendida": 0,
        "ticket_promedio": "0.00",
        "numero_ventas": 0,
        "ventas_por_categoria": [],
    }
    app.state.engine.dispose()
