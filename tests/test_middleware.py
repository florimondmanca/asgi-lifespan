import typing

import pytest

from asgi_lifespan import LifespanMiddleware
from asgi_lifespan._types import Message, Receive, Scope, Send


@pytest.mark.usefixtures("concurrency")
async def test_lifespan_middleware() -> None:
    scopes: typing.List[Scope] = []

    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        assert scope["type"] == "http"
        scopes.append(scope)

    async def lifespan(scope: Scope, receive: Receive, send: Send) -> None:
        assert scope["type"] == "lifespan"
        scopes.append(scope)

    app = LifespanMiddleware(app, lifespan=lifespan)

    async def receive() -> Message:
        pass  # pragma: no cover

    async def send(message: Message) -> None:
        pass  # pragma: no cover

    await app({"type": "lifespan"}, receive, send)
    await app({"type": "http"}, receive, send)
    assert scopes == [{"type": "lifespan"}, {"type": "http"}]
