import typing

import anyio
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


async def slow_startup(
    scope: dict, receive: typing.Callable, send: typing.Callable
) -> None:
    message = await receive()
    assert message["type"] == "lifespan.startup"
    await anyio.sleep(0.05)
    # ...


async def slow_shutdown(
    scope: dict, receive: typing.Callable, send: typing.Callable
) -> None:
    message = await receive()
    assert message["type"] == "lifespan.startup"
    await send({"type": "lifespan.startup.complete"})

    message = await receive()
    assert message["type"] == "lifespan.shutdown"
    await anyio.sleep(0.05)
    # ...


@pytest.mark.anyio
@pytest.mark.parametrize("app", [slow_startup, slow_shutdown])
async def test_lifespan_timeout(app: typing.Callable) -> None:
    async with anyio.move_on_after(0.02) as cancel_scope:
        with pytest.raises(TimeoutError):
            async with LifespanManager(
                app, startup_timeout=0.01, shutdown_timeout=0.01
            ):
                pass
    assert not cancel_scope.cancel_called


@pytest.mark.anyio
@pytest.mark.parametrize("app", [slow_startup, slow_shutdown])
async def test_lifespan_no_timeout(app: typing.Callable) -> None:
    async with anyio.move_on_after(0.02) as cancel_scope:
        async with LifespanManager(app, startup_timeout=None, shutdown_timeout=None):
            pass
    assert cancel_scope.cancel_called
