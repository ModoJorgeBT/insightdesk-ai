import { lazy, Suspense, useCallback, useEffect, useMemo, useState } from "react";
import { getIndicadores, getProductos, getVentas, postVenta } from "./api.js";
import { AgentPanel } from "./components/AgentPanel.jsx";
import { ErrorNotice } from "./components/ErrorNotice.jsx";
import { RecentSalesTable } from "./components/RecentSalesTable.jsx";
import { SectionCard } from "./components/SectionCard.jsx";
import { StatCard } from "./components/StatCard.jsx";

const currencyNumber = new Intl.NumberFormat("es-CR", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});
const wholeNumber = new Intl.NumberFormat("es-CR");
const SalesCategoryChart = lazy(() => import("./components/SalesCategoryChart.jsx"));

function formatAmount(value) {
  return currencyNumber.format(Number(value ?? 0));
}

function formatCount(value) {
  return wholeNumber.format(Number(value ?? 0));
}

function LoadingDashboard() {
  return (
    <div className="loading-screen" role="status" aria-live="polite">
      <span className="loading-spinner" />
      <p>Cargando tu resumen comercial…</p>
    </div>
  );
}

function ChartLoading() {
  return (
    <div className="empty-chart" role="status">
      <span className="loading-spinner" />
      <p>Cargando gráfico…</p>
    </div>
  );
}

export default function App() {
  const [dashboard, setDashboard] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [saveError, setSaveError] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [selectedProductId, setSelectedProductId] = useState("");
  const [quantity, setQuantity] = useState("1");
  const [unitPrice, setUnitPrice] = useState("");
  const [formError, setFormError] = useState("");

  const loadDashboard = useCallback(async () => {
    setIsLoading(true);
    setLoadError("");
    try {
      const [indicadores, productos, ventas] = await Promise.all([
        getIndicadores(),
        getProductos(),
        getVentas(),
      ]);
      setDashboard({ indicadores, productos, ventas });
    } catch (error) {
      setLoadError(error.message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  const productById = useMemo(
    () => new Map((dashboard?.productos ?? []).map((product) => [product.id, product])),
    [dashboard?.productos],
  );
  const recentSales = useMemo(
    () =>
      [...(dashboard?.ventas ?? [])]
        .sort((a, b) => new Date(b.fecha) - new Date(a.fecha) || b.id - a.id)
        .slice(0, 7),
    [dashboard?.ventas],
  );

  function handleProductChange(event) {
    const id = event.target.value;
    setSelectedProductId(id);
    setFormError("");
    setSaveError("");
    setUnitPrice(id ? String(productById.get(Number(id))?.precio ?? "") : "");
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setFormError("");
    setSaveError("");

    const parsedQuantity = Number(quantity);
    const parsedPrice = Number(unitPrice);
    if (!selectedProductId) {
      setFormError("Selecciona un producto para registrar la venta.");
      return;
    }
    if (!Number.isInteger(parsedQuantity) || parsedQuantity < 1) {
      setFormError("La cantidad debe ser un número entero mayor que cero.");
      return;
    }
    if (!Number.isFinite(parsedPrice) || parsedPrice <= 0) {
      setFormError("El precio unitario debe ser mayor que cero.");
      return;
    }

    setIsSaving(true);
    try {
      await postVenta({
        producto_id: Number(selectedProductId),
        cantidad: parsedQuantity,
        precio_unitario: parsedPrice.toFixed(2),
      });
      setSelectedProductId("");
      setQuantity("1");
      setUnitPrice("");
      await loadDashboard();
    } catch (error) {
      setSaveError(error.message);
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="#" aria-label="InsightDesk AI, inicio">
          <span className="brand-mark" aria-hidden="true">
            <svg viewBox="0 0 32 32" fill="none">
              <path d="M5 22.5 12.2 15l4.8 4.5L27 8" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M20 8h7v7" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </span>
          <span className="brand-name">insight<span>desk</span></span>
        </a>

        <div className="sidebar-label">ESPACIO DE TRABAJO</div>
        <nav className="side-nav" aria-label="Navegación principal">
          <a className="nav-item nav-item-active" href="#resumen" aria-current="page">
            <span className="nav-icon" aria-hidden="true">▦</span>
            <span>Resumen</span>
          </a>
          <a className="nav-item" href="#ventas">
            <span className="nav-icon" aria-hidden="true">↗</span>
            <span>Ventas</span>
          </a>
          <a className="nav-item" href="#productos">
            <span className="nav-icon" aria-hidden="true">◫</span>
            <span>Productos</span>
          </a>
          <a className="nav-item nav-item-muted" href="#asistente">
            <span className="nav-icon" aria-hidden="true">✳</span>
            <span>Asistente IA</span>
            <span className="nav-soon">Pronto</span>
          </a>
        </nav>

        <div className="sidebar-spacer" />
        <div className="sidebar-status">
          <span className="status-dot" />
          <span>Datos conectados</span>
        </div>
        <div className="profile-card">
          <div className="profile-avatar">ID</div>
          <div className="profile-copy">
            <strong>InsightDesk</strong>
            <span>Panel comercial</span>
          </div>
          <span className="profile-menu" aria-hidden="true">···</span>
        </div>
      </aside>

      <main className="main-content" id="resumen">
        <header className="topbar">
          <div className="breadcrumb"><span>Workspace</span><span className="breadcrumb-slash">/</span><strong>Resumen</strong></div>
          <div className="topbar-actions">
            <span className="live-indicator"><span className="status-dot" /> Actualizado desde la API</span>
            <div className="topbar-avatar" aria-hidden="true">ID</div>
          </div>
        </header>

        <div className="dashboard-content">
          <section className="welcome-row">
            <div>
              <p className="eyebrow">PANEL COMERCIAL</p>
              <h1>Tu negocio, de un vistazo<span className="title-period">.</span></h1>
              <p className="welcome-subtitle">Indicadores y actividad reciente de tus ventas.</p>
            </div>
            <a className="date-chip" href="#ventas">
              <span className="calendar-icon" aria-hidden="true">▦</span>
              Datos disponibles
            </a>
          </section>

          {loadError && (
            <ErrorNotice
              message={loadError}
              onRetry={loadDashboard}
              retryLabel="Reintentar"
              title="No se pudo cargar el dashboard"
            />
          )}

          {!dashboard && isLoading ? (
            <LoadingDashboard />
          ) : dashboard ? (
            <>
              {loadError && <p className="stale-data-note">Se muestran los últimos datos cargados; la actualización falló.</p>}
              <section className="stats-grid" aria-label="Indicadores principales">
                <StatCard
                  label="Ingresos totales"
                  value={formatAmount(dashboard.indicadores.ingresos_totales)}
                  icon="↗"
                  tone="green"
                  detail="Suma de ventas registradas"
                />
                <StatCard
                  label="Unidades vendidas"
                  value={formatCount(dashboard.indicadores.cantidad_vendida)}
                  icon="▤"
                  tone="blue"
                  detail="Unidades en todas las ventas"
                />
                <StatCard
                  label="Ticket promedio"
                  value={formatAmount(dashboard.indicadores.ticket_promedio)}
                  icon="◉"
                  tone="purple"
                  detail="Promedio por transacción"
                />
              </section>

              <section className="analytics-grid">
                <SectionCard
                  id="categorias"
                  title="Ventas por categoría"
                  subtitle="Ingresos registrados en cada categoría"
                  className="chart-card"
                  action={<span className="chart-legend"><span /> Ingresos</span>}
                >
                  <Suspense fallback={<ChartLoading />}>
                    <SalesCategoryChart categories={dashboard.indicadores.ventas_por_categoria} />
                  </Suspense>
                </SectionCard>
                <AgentPanel />
              </section>

              <section className="lower-grid">
                <SectionCard
                  id="ventas"
                  title="Ventas recientes"
                  subtitle="Últimas transacciones registradas"
                  className="table-card"
                  action={<span className="record-count">{formatCount(dashboard.ventas.length)} registros</span>}
                >
                  <RecentSalesTable sales={recentSales} productsById={productById} />
                </SectionCard>

                <SectionCard
                  id="productos"
                  title="Registrar venta"
                  subtitle="Agrega una nueva transacción"
                  className="form-card"
                >
                  <form className="sale-form" onSubmit={handleSubmit}>
                    <label className="field-label" htmlFor="sale-product">Producto</label>
                    <select
                      id="sale-product"
                      value={selectedProductId}
                      onChange={handleProductChange}
                      required
                      disabled={isSaving || dashboard.productos.length === 0}
                    >
                      <option value="">Selecciona un producto</option>
                      {dashboard.productos.map((product) => (
                        <option key={product.id} value={product.id}>
                          {product.nombre} · {product.categoria}
                        </option>
                      ))}
                    </select>

                    <div className="form-fields-row">
                      <div>
                        <label className="field-label" htmlFor="sale-quantity">Cantidad</label>
                        <input
                          id="sale-quantity"
                          type="number"
                          min="1"
                          step="1"
                          inputMode="numeric"
                          value={quantity}
                          onChange={(event) => setQuantity(event.target.value)}
                          required
                          disabled={isSaving}
                        />
                      </div>
                      <div>
                        <label className="field-label" htmlFor="sale-price">Precio unitario</label>
                        <input
                          id="sale-price"
                          type="number"
                          min="0.01"
                          step="0.01"
                          inputMode="decimal"
                          placeholder="0.00"
                          value={unitPrice}
                          onChange={(event) => setUnitPrice(event.target.value)}
                          required
                          disabled={isSaving}
                        />
                      </div>
                    </div>

                    {formError && <p className="form-message form-message-error" role="alert">{formError}</p>}
                    {saveError && <p className="form-message form-message-error" role="alert">{saveError}</p>}
                    {dashboard.productos.length === 0 && (
                      <p className="form-message">Registra un producto en la API para poder crear ventas.</p>
                    )}
                    <button className="primary-button" type="submit" disabled={isSaving || dashboard.productos.length === 0}>
                      {isSaving ? <><span className="button-spinner" /> Guardando…</> : <><span aria-hidden="true">＋</span> Registrar venta</>}
                    </button>
                  </form>
                </SectionCard>
              </section>
            </>
          ) : null}

          <footer className="page-footer">
            <span>InsightDesk AI</span>
            <span>Información obtenida de tu API comercial</span>
          </footer>
        </div>
      </main>
    </div>
  );
}
