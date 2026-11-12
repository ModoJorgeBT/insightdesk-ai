import os
from types import SimpleNamespace

import httpx
import pytest
from google.genai import errors, types

from app.agent import AgentFailure, GeminiSalesAgent, load_backend_environment
from app.agent_tools import (
    consultar_resumen_ventas,
    consultar_ventas_por_categoria,
    consultar_ventas_por_producto,
)


class FakeModels:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def generate_content(self, **kwargs):
        kwargs["contents"] = list(kwargs["contents"])
        self.calls.append(kwargs)
        response = self.responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response


class FakeClient:
    def __init__(self, responses):
        self.models = FakeModels(responses)
        self.closed = False

    def close(self):
        self.closed = True


def function_response(name, arguments):
    part = types.Part.from_function_call(name=name, args=arguments)
    return SimpleNamespace(
        candidates=[SimpleNamespace(content=types.Content(role="model", parts=[part]))],
        text=None,
    )


def text_response(text):
    return SimpleNamespace(candidates=[], text=text)


def test_backend_dotenv_loads_key_without_overriding_process_environment(tmp_path, monkeypatch) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("GEMINI_API_KEY=dotenv-test-key\n", encoding="utf-8")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    load_backend_environment(env_file)

    assert os.environ["GEMINI_API_KEY"] == "dotenv-test-key"
    monkeypatch.setenv("GEMINI_API_KEY", "process-test-key")
    load_backend_environment(env_file)
    assert os.environ["GEMINI_API_KEY"] == "process-test-key"


def test_read_only_tools_return_real_database_results(api) -> None:
    with api.app.state.session_factory() as session:
        summary = consultar_resumen_ventas(session, {})
        product = consultar_ventas_por_producto(session, {"producto": "Laptop Pro"})
        category = consultar_ventas_por_categoria(session, {"categoria": "Tecnología"})
        injection_attempt = consultar_ventas_por_producto(
            session,
            {"producto": "' OR 1=1 --"},
        )

    assert summary["numero_ventas"] == 50
    assert summary["unidades_vendidas"] == 225
    assert summary["ingresos_totales"] == "114825.00"
    assert product["resultados"]
    assert all(item["producto"] == "Laptop Pro" for item in product["resultados"])
    assert category["resultados"][0]["categoria"] == "Tecnología"
    assert injection_attempt["resultados"] == []


def test_chat_uses_real_function_call_and_returns_tool_usage(api, monkeypatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-only-key")
    client = FakeClient(
        [
            function_response("consultar_resumen_ventas", {}),
            text_response(
                "Las ventas suman 114825.00 en ingresos y 225 unidades. "
                "La categoría con más ingresos es Tecnología; considera priorizar su inventario."
            ),
        ]
    )
    agent = GeminiSalesAgent(client_factory=lambda **_: client)
    api.app.state.agent_service = agent

    status_code, response = api.request(
        "POST",
        "/api/agente/chat",
        {"mensaje": "Resume las ventas y recomienda una acción comercial."},
    )

    assert status_code == 200
    assert "114825.00" in response["respuesta"]
    assert response["herramientas_usadas"] == ["consultar_resumen_ventas"]
    assert len(client.models.calls) == 2
    initial_config = client.models.calls[0]["config"]
    assert initial_config.tool_config.function_calling_config.mode == "ANY"
    assert initial_config.automatic_function_calling.disable is True
    assert client.models.calls[1]["contents"][-1].parts[0].function_response.response[
        "ingresos_totales"
    ] == "114825.00"
    assert client.closed


def test_chat_calls_product_tool_and_validates_tool_arguments(api, monkeypatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-only-key")
    client = FakeClient(
        [
            function_response(
                "consultar_ventas_por_producto",
                {"producto": "Laptop Pro", "sql": "DROP TABLE ventas"},
            ),
            function_response(
                "consultar_ventas_por_producto",
                {"producto": "Laptop Pro"},
            ),
            text_response("Consulté las ventas del producto solicitado."),
        ]
    )
    api.app.state.agent_service = GeminiSalesAgent(client_factory=lambda **_: client)

    status_code, response = api.request(
        "POST",
        "/api/agente/chat",
        {"mensaje": "¿Cómo se ha vendido Laptop Pro?"},
    )

    assert status_code == 200
    assert response["herramientas_usadas"] == ["consultar_ventas_por_producto"]
    first_tool_response = client.models.calls[1]["contents"][-1].parts[0].function_response.response
    assert "error" in first_tool_response
    assert "resultados" in client.models.calls[2]["contents"][-1].parts[0].function_response.response


def test_chat_rejects_invalid_request_and_missing_api_key(api, monkeypatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    invalid_status, invalid_response = api.request("POST", "/api/agente/chat", {"mensaje": " "})
    missing_key_status, missing_key_response = api.request(
        "POST",
        "/api/agente/chat",
        {"mensaje": "Resume mis ventas."},
    )

    assert invalid_status == 422
    assert missing_key_status == 503
    assert "GEMINI_API_KEY" in missing_key_response["detail"]
    assert "API key" not in str(invalid_response)


@pytest.mark.parametrize(
    ("provider_error", "expected_status", "expected_detail"),
    [
        (
            errors.APIError(429, {"error": {"status": "RESOURCE_EXHAUSTED"}}),
            429,
            "cuota",
        ),
        (errors.APIError(401, {"error": {"status": "UNAUTHENTICATED"}}), 502, "autenticación"),
        (errors.APIError(504, {"error": {"status": "DEADLINE_EXCEEDED"}}), 504, "tiempo de respuesta"),
        (httpx.ReadTimeout("sensitive provider request"), 504, "tiempo de espera"),
    ],
)
def test_chat_maps_provider_auth_quota_and_timeout_errors(
    api,
    monkeypatch,
    provider_error,
    expected_status,
    expected_detail,
) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "never-return-this-secret")
    client = FakeClient([provider_error])
    api.app.state.agent_service = GeminiSalesAgent(client_factory=lambda **_: client)

    status_code, response = api.request(
        "POST",
        "/api/agente/chat",
        {"mensaje": "Resume mis ventas."},
    )

    assert status_code == expected_status
    assert expected_detail in response["detail"]
    assert "never-return-this-secret" not in str(response)
    assert "sensitive provider request" not in str(response)
    assert client.closed


def test_chat_rejects_empty_response_without_exposing_provider_details(api, monkeypatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-only-key")
    client = FakeClient(
        [
            function_response("consultar_resumen_ventas", {}),
            text_response("  "),
        ]
    )
    api.app.state.agent_service = GeminiSalesAgent(client_factory=lambda **_: client)

    status_code, response = api.request(
        "POST",
        "/api/agente/chat",
        {"mensaje": "Resume las ventas."},
    )

    assert status_code == 502
    assert "respuesta vacía" in response["detail"]
    assert "test-only-key" not in str(response)
    assert client.closed


def test_chat_does_not_execute_unlisted_function_calls(api, monkeypatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-only-key")
    client = FakeClient(
        [
            function_response("ejecutar_sql", {"query": "DROP TABLE ventas"}),
            text_response("Terminado."),
        ]
    )
    api.app.state.agent_service = GeminiSalesAgent(client_factory=lambda **_: client)

    status_code, response = api.request(
        "POST",
        "/api/agente/chat",
        {"mensaje": "Haz una consulta."},
    )

    assert status_code == 502
    assert "no consultó los datos" in response["detail"]
    with api.app.state.session_factory() as session:
        summary = consultar_resumen_ventas(session, {})
    assert summary["numero_ventas"] == 50
