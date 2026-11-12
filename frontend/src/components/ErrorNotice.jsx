export function ErrorNotice({ message, onRetry, retryLabel = "Reintentar", title = "Ocurrió un error" }) {
  return (
    <div className="error-notice" role="alert">
      <span className="error-symbol" aria-hidden="true">!</span>
      <div className="error-copy">
        <strong>{title}</strong>
        <span>{message}</span>
      </div>
      {onRetry && <button className="retry-button" type="button" onClick={onRetry}>{retryLabel}</button>}
    </div>
  );
}
