import asyncio
import json
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI

from app.main import create_app


class ASGIClient:
    def __init__(self, app: FastAPI):
        self.app = app

    def request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> tuple[int, Any]:
        body = json.dumps(payload).encode("utf-8") if payload is not None else b""
        messages: list[dict[str, Any]] = []
        request_sent = False

        async def receive() -> dict[str, Any]:
            nonlocal request_sent
            if request_sent:
                return {"type": "http.disconnect"}
            request_sent = True
            return {"type": "http.request", "body": body, "more_body": False}

        async def send(message: dict[str, Any]) -> None:
            messages.append(message)

        scope = {
            "type": "http",
            "asgi": {"version": "3.0", "spec_version": "2.0"},
            "http_version": "1.1",
            "method": method,
            "scheme": "http",
            "path": path,
            "raw_path": path.encode("ascii"),
            "query_string": b"",
            "root_path": "",
            "headers": [(b"content-type", b"application/json")],
            "server": ("testserver", 80),
            "client": ("testclient", 123),
            "state": {},
        }
        asyncio.run(self.app(scope, receive, send))
        response = next(message for message in messages if message["type"] == "http.response.start")
        response_body = b"".join(
            message.get("body", b"")
            for message in messages
            if message["type"] == "http.response.body"
        )
        return response["status"], json.loads(response_body) if response_body else None


def run_lifespan(app: FastAPI) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    incoming = iter(
        [
            {"type": "lifespan.startup"},
            {"type": "lifespan.shutdown"},
        ]
    )

    async def receive() -> dict[str, Any]:
        return next(incoming)

    async def send(message: dict[str, Any]) -> None:
        messages.append(message)

    asyncio.run(
        app(
            {"type": "lifespan", "asgi": {"version": "3.0", "spec_version": "2.0"}},
            receive,
            send,
        )
    )
    return messages


@pytest.fixture
def api(tmp_path: Path) -> Generator[ASGIClient, None, None]:
    app = create_app(f"sqlite:///{(tmp_path / 'test.db').as_posix()}")
    lifecycle_messages = run_lifespan(app)
    assert [message["type"] for message in lifecycle_messages] == [
        "lifespan.startup.complete",
        "lifespan.shutdown.complete",
    ]
    yield ASGIClient(app)
    app.state.engine.dispose()
