import { useState } from "react";
import { postChatMessage } from "../api.js";

const toolLabels = {
  consultar_resumen_ventas: "Resumen de ventas",
  consultar_ventas_por_producto: "Ventas por producto",
  consultar_ventas_por_categoria: "Ventas por categoría",
};

export function AgentPanel() {
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState("");
  const [error, setError] = useState("");
  const [isSending, setIsSending] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    const message = draft.trim();
    if (!message || isSending) return;

    setMessages((current) => [...current, { role: "user", text: message }].slice(-20));
    setDraft("");
    setError("");
    setIsSending(true);
    try {
      const response = await postChatMessage(message);
      setMessages((current) =>
        [...current, {
          role: "assistant",
          text: response.respuesta,
          tools: response.herramientas_usadas,
        }].slice(-20),
      );
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setIsSending(false);
    }
  }

  return (
    <aside className="agent-card" id="asistente" aria-labelledby="agent-title">
      <header className="agent-header">
        <div className="agent-orb" aria-hidden="true"><span>✳</span></div>
        <div className="agent-heading">
          <h2 id="agent-title">Asistente comercial</h2>
          <div className="agent-status"><span className="agent-status-dot" /> Conectado a tus datos</div>
        </div>
      </header>

      <div className="agent-messages" aria-live="polite" aria-label="Conversación con el asistente">
        {messages.length === 0 && (
          <div className="agent-empty">
            <span className="agent-empty-icon" aria-hidden="true">✦</span>
            <strong>Pregunta sobre tus ventas</strong>
            <span>El asistente consultará los datos guardados para responder.</span>
          </div>
        )}
        {messages.map((message, index) => (
          <article className={`chat-message chat-message-${message.role}`} key={`${index}-${message.role}`}>
            <p>{message.text}</p>
            {message.tools?.length > 0 && (
              <span className="chat-source">
                Datos consultados: {[...new Set(message.tools)].map((tool) => toolLabels[tool] ?? tool).join(", ")}
              </span>
            )}
          </article>
        ))}
        {isSending && (
          <div className="chat-message chat-message-assistant" role="status">
            <span className="chat-thinking"><span /><span /><span /></span>
            <span className="chat-thinking-label">Consultando la información…</span>
          </div>
        )}
      </div>

      {error && <p className="agent-error" role="alert">{error}</p>}

      <form className="agent-form" onSubmit={handleSubmit}>
        <label className="visually-hidden" htmlFor="agent-message">Pregunta sobre tus ventas</label>
        <textarea
          id="agent-message"
          rows="2"
          maxLength="2000"
          placeholder="Escribe tu pregunta…"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          disabled={isSending}
        />
        <div className="agent-form-footer">
          <span>Las respuestas se basan en tus datos comerciales.</span>
          <button type="submit" disabled={isSending || !draft.trim()} aria-label="Enviar pregunta">
            {isSending ? <span className="button-spinner" /> : <span aria-hidden="true">↑</span>}
          </button>
        </div>
      </form>
    </aside>
  );
}
