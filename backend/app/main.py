from contextlib import asynccontextmanager
from decimal import Decimal, ROUND_HALF_UP
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.agent import AgentFailure, AgentService, GeminiSalesAgent
from app.database import create_database_engine, create_session_factory, get_db
from app.models import Base, Producto, Venta
from app.schemas import (
    AgentChatRequest,
    AgentChatResponse,
    CategoriaIndicadores,
    IndicadoresRead,
    ProductoCreate,
    ProductoRead,
    VentaCreate,
    VentaRead,
)
from app.seed import seed_database


CENTAVOS = Decimal("0.01")


def moneda(value: Decimal | float | int | None) -> Decimal:
    return Decimal(str(value or 0)).quantize(CENTAVOS, rounding=ROUND_HALF_UP)


def create_app(
    database_url: str | None = None,
    seed_on_startup: bool = True,
    agent_service: AgentService | None = None,
) -> FastAPI:
    engine = create_database_engine(database_url)
    session_factory = create_session_factory(engine)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        Base.metadata.create_all(bind=engine)
        if seed_on_startup:
            with session_factory() as session:
                seed_database(session)
        yield
        engine.dispose()

    app = FastAPI(title="InsightDesk AI API", lifespan=lifespan)
    app.state.engine = engine
    app.state.session_factory = session_factory
    app.state.agent_service = agent_service or GeminiSalesAgent()
    database = Annotated[Session, Depends(get_db)]

    @app.get("/api/productos", response_model=list[ProductoRead])
    def listar_productos(session: database) -> list[Producto]:
        return list(session.scalars(select(Producto).order_by(Producto.id)))

    @app.post(
        "/api/productos",
        response_model=ProductoRead,
        status_code=status.HTTP_201_CREATED,
    )
    def crear_producto(payload: ProductoCreate, session: database) -> Producto:
        producto = Producto(**payload.model_dump())
        session.add(producto)
        session.commit()
        session.refresh(producto)
        return producto

    @app.get("/api/ventas", response_model=list[VentaRead])
    def listar_ventas(session: database) -> list[Venta]:
        return list(session.scalars(select(Venta).order_by(Venta.id)))

    @app.post(
        "/api/ventas",
        response_model=VentaRead,
        status_code=status.HTTP_201_CREATED,
    )
    def crear_venta(payload: VentaCreate, session: database) -> Venta:
        producto = session.get(Producto, payload.producto_id)
        if producto is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El producto indicado no existe",
            )

        venta = Venta(**payload.model_dump(exclude_none=True))
        session.add(venta)
        session.commit()
        session.refresh(venta)
        return venta

    @app.get("/api/indicadores", response_model=IndicadoresRead)
    def obtener_indicadores(session: database) -> IndicadoresRead:
        resumen = session.execute(
            select(
                func.coalesce(func.sum(Venta.cantidad * Venta.precio_unitario), 0),
                func.coalesce(func.sum(Venta.cantidad), 0),
                func.count(Venta.id),
            )
        ).one()
        ingresos_totales = moneda(resumen[0])
        cantidad_vendida = int(resumen[1])
        numero_ventas = int(resumen[2])
        ticket_promedio = moneda(ingresos_totales / numero_ventas) if numero_ventas else Decimal("0.00")

        filas_categoria = session.execute(
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
        ventas_por_categoria = [
            CategoriaIndicadores(
                categoria=categoria,
                ingresos=moneda(ingresos),
                cantidad_vendida=int(unidades),
                numero_ventas=int(ventas),
            )
            for categoria, ingresos, unidades, ventas in filas_categoria
        ]
        return IndicadoresRead(
            ingresos_totales=ingresos_totales,
            cantidad_vendida=cantidad_vendida,
            ticket_promedio=ticket_promedio,
            numero_ventas=numero_ventas,
            ventas_por_categoria=ventas_por_categoria,
        )

    @app.post("/api/agente/chat", response_model=AgentChatResponse)
    def chat_agente(payload: AgentChatRequest, session: database) -> AgentChatResponse:
        try:
            answer, used_tools = app.state.agent_service.chat(payload.mensaje, session)
        except AgentFailure as error:
            raise HTTPException(status_code=error.status_code, detail=error.detail) from None
        return AgentChatResponse(respuesta=answer, herramientas_usadas=used_tools)

    return app


app = create_app()
