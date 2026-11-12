const dateFormatter = new Intl.DateTimeFormat("es-CR", {
  day: "2-digit",
  month: "short",
  year: "numeric",
});
const numberFormatter = new Intl.NumberFormat("es-CR", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

function formatDate(value) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "Fecha no disponible" : dateFormatter.format(date);
}

function formatAmount(value) {
  return numberFormatter.format(Number(value ?? 0));
}

export function RecentSalesTable({ sales, productsById }) {
  if (sales.length === 0) {
    return (
      <div className="empty-table">
        <span className="empty-table-icon" aria-hidden="true">↗</span>
        <strong>Aún no hay ventas</strong>
        <span>Cuando registres una venta, aparecerá aquí.</span>
      </div>
    );
  }

  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            <th>PRODUCTO</th>
            <th>FECHA</th>
            <th>CANTIDAD</th>
            <th className="amount-cell">INGRESOS</th>
          </tr>
        </thead>
        <tbody>
          {sales.map((sale) => {
            const product = productsById.get(sale.producto_id);
            return (
              <tr key={sale.id}>
                <td>
                  <div className="product-cell">
                    <span className="product-avatar" aria-hidden="true">
                      {(product?.nombre ?? "P").charAt(0).toUpperCase()}
                    </span>
                    <span className="product-cell-copy">
                      <strong>{product?.nombre ?? `Producto #${sale.producto_id}`}</strong>
                      <span>{product?.categoria ?? "Categoría"}</span>
                    </span>
                  </div>
                </td>
                <td className="date-cell">{formatDate(sale.fecha)}</td>
                <td><span className="quantity-pill">{sale.cantidad} uds.</span></td>
                <td className="amount-cell amount-value">
                  {formatAmount(Number(sale.cantidad) * Number(sale.precio_unitario))}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
