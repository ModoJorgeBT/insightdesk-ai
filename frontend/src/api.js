const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers: {
        Accept: "application/json",
        ...(options.body ? { "Content-Type": "application/json" } : {}),
        ...options.headers,
      },
    });
  } catch {
    throw new Error("No hay conexión con el backend. Verifica que la API esté en ejecución e inténtalo de nuevo.");
  }

  let payload = null;
  try {
    payload = await response.json();
  } catch {
    if (response.ok) {
      throw new Error("El backend devolvió una respuesta que no es JSON válido.");
    }
  }
  if (!response.ok) {
    const detail = payload?.detail;
    const message = Array.isArray(detail)
      ? detail.map((item) => item.msg).join(". ")
      : typeof detail === "string"
        ? detail
        : `La API respondió con el estado ${response.status}.`;
    throw new Error(message);
  }
  return payload;
}

export function getIndicadores() {
  return request("/api/indicadores");
}

export function getProductos() {
  return request("/api/productos");
}

export function getVentas() {
  return request("/api/ventas");
}

export function postVenta(sale) {
  return request("/api/ventas", {
    method: "POST",
    body: JSON.stringify(sale),
  });
}

export function postChatMessage(mensaje) {
  return request("/api/agente/chat", {
    method: "POST",
    body: JSON.stringify({ mensaje }),
  });
}
