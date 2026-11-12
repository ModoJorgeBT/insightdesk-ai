export function SectionCard({ id, title, subtitle, action, className = "", children }) {
  return (
    <article className={`section-card ${className}`} id={id}>
      <header className="section-card-header">
        <div>
          <h2>{title}</h2>
          <p>{subtitle}</p>
        </div>
        {action && <div className="section-card-action">{action}</div>}
      </header>
      {children}
    </article>
  );
}
