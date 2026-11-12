export function StatCard({ label, value, icon, tone, detail }) {
  return (
    <article className="stat-card">
      <div className="stat-card-top">
        <span className="stat-label">{label}</span>
        <span className={`stat-icon stat-icon-${tone}`} aria-hidden="true">{icon}</span>
      </div>
      <div className="stat-value" title={value}>{value}</div>
      <div className="stat-detail">{detail}</div>
      <span className={`stat-accent stat-accent-${tone}`} />
    </article>
  );
}
