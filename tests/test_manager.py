import typing

import pytest

from asgi_lifespan import Lifespan, LifespanManager, LifespanNotSupported

from .compat import nullcontext


@pytest.mark.anyio
async def test_lifespan_not_supported() -> None:
    async def app(scope: dict, receive: typing.Callable, send: typing.Callable) -> None:
        assert scope["type"] == "http"

    with pytest.raises(LifespanNotSupported):
        async with LifespanManager(app):
            pass  # pragma: no cover


@pytest.mark.anyio
@pytest.mark.parametrize("startup_exception", (None, ValueError))
async def test_lifespan_manager(
    startup_exception: typing.Optional[typing.Type[BaseException]]
) -> None:
    lifespan = Lifespan()

    if startup_exception is not None:

        @lifespan.on_event("startup")
        async def startup() -> None:
            assert startup_exception is not None
            raise startup_exception

    received_lifespan_events: typing.List[str] = []
    sent_lifespan_events: typing.List[str] = []

    async def app(scope: dict, receive: typing.Callable, send: typing.Callable) -> None:
        assert scope["type"] == "lifespan"

        async def _receive() -> dict:
            message = await receive()
            received_lifespan_events.append(message["type"])
            return message

        async def _send(message: dict) -> None:
            sent_lifespan_events.append(message["type"])
            await send(message)

        await lifespan(scope, _receive, _send)

    with pytest.raises(startup_exception) if startup_exception else nullcontext():
        async with LifespanManager(app) as ctx:
            # NOTE: this block will not get executed if in case of startup exception.
            assert ctx is None
            assert not startup_exception
            assert received_lifespan_events == ["lifespan.startup"]
            assert sent_lifespan_events == ["lifespan.startup.complete"]

    if startup_exception:
        assert received_lifespan_events == ["lifespan.startup"]
        assert sent_lifespan_events == ["lifespan.startup.failed"]
    else:
        assert received_lifespan_events == ["lifespan.startup", "lifespan.shutdown"]
        assert sent_lifespan_events == [
            "lifespan.startup.complete",
            "lifespan.shutdown.complete",
        ]
