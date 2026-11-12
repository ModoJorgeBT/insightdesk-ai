import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const currencyNumber = new Intl.NumberFormat("es-CR", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});
const wholeNumber = new Intl.NumberFormat("es-CR");

function formatAmount(value) {
  return currencyNumber.format(Number(value ?? 0));
}

function formatCount(value) {
  return wholeNumber.format(Number(value ?? 0));
}

export default function SalesCategoryChart({ categories }) {
  const chartData = categories.map((item) => ({
    categoria: item.categoria,
    ingresos: Number(item.ingresos),
  }));
  const hasSales = chartData.some((item) => item.ingresos > 0);

  if (!hasSales) {
    return (
      <div className="empty-chart">
        <span className="empty-chart-icon" aria-hidden="true">◌</span>
        <p>Aún no hay ventas para mostrar por categoría.</p>
      </div>
    );
  }

  return (
    <div className="chart-wrap" role="img" aria-label="Ingresos por categoría">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={chartData} margin={{ top: 10, right: 12, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="salesGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#15a88a" stopOpacity={0.22} />
              <stop offset="96%" stopColor="#15a88a" stopOpacity={0.015} />
            </linearGradient>
          </defs>
          <CartesianGrid vertical={false} stroke="#edf0f4" strokeDasharray="4 5" />
          <XAxis
            dataKey="categoria"
            axisLine={false}
            tickLine={false}
            tick={{ fill: "#87909e", fontSize: 12 }}
            tickMargin={13}
          />
          <YAxis
            axisLine={false}
            tickLine={false}
            tick={{ fill: "#87909e", fontSize: 11 }}
            tickFormatter={formatCount}
            width={53}
          />
          <Tooltip
            cursor={{ stroke: "#dce6e3", strokeDasharray: "4 4" }}
            contentStyle={{
              border: "1px solid #e8edf0",
              borderRadius: 12,
              boxShadow: "0 8px 24px rgb(23 39 48 / 10%)",
              fontSize: 12,
            }}
            formatter={(value, name) => [formatAmount(value), name]}
            labelStyle={{ color: "#283648", fontWeight: 700, marginBottom: 5 }}
          />
          <Area
            type="monotone"
            dataKey="ingresos"
            name="Ingresos"
            stroke="#129879"
            strokeWidth={3}
            fill="url(#salesGradient)"
            activeDot={{ r: 5, strokeWidth: 3, stroke: "#e5f6f1" }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
