import typing

import pytest

from asgi_lifespan import LifespanMiddleware


@pytest.mark.usefixtures("concurrency")
async def test_lifespan_middleware() -> None:
    scopes: typing.List[dict] = []

    async def app(scope: dict, receive: typing.Callable, send: typing.Callable) -> None:
        assert scope["type"] == "http"
        scopes.append(scope)

    async def lifespan(
        scope: dict, receive: typing.Callable, send: typing.Callable
    ) -> None:
        assert scope["type"] == "lifespan"
        scopes.append(scope)

    app = LifespanMiddleware(app, lifespan=lifespan)

    async def receive() -> dict:
        pass  # pragma: no cover

    async def send(message: dict) -> None:
        pass  # pragma: no cover

    await app({"type": "lifespan"}, receive, send)
    await app({"type": "http"}, receive, send)
    assert scopes == [{"type": "lifespan"}, {"type": "http"}]
