import contextlib
import typing

import httpx as httpx
import pytest
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response
from starlette.routing import Route, Router

from asgi_lifespan import LifespanManager, LifespanNotSupported
from asgi_lifespan._concurrency import detect_concurrency_backend
from asgi_lifespan._types import ASGIApp, Message, Receive, Scope, Send

from . import concurrency
from .compat import ExceptionGroup


class StartupFailed(Exception):
    pass


class BodyFailed(Exception):
    pass


class ShutdownFailed(Exception):
    pass


@pytest.mark.usefixtures("concurrency")
@pytest.mark.parametrize("startup_exception", (None, StartupFailed))
@pytest.mark.parametrize("body_exception", (None, BodyFailed))
@pytest.mark.parametrize("shutdown_exception", (None, ShutdownFailed))
async def test_lifespan_manager(
    concurrency: str,
    startup_exception: typing.Optional[typing.Type[BaseException]],
    body_exception: typing.Optional[typing.Type[BaseException]],
    shutdown_exception: typing.Optional[typing.Type[BaseException]],
) -> None:
    # Setup failing event handlers.

    on_startup: list = []
    on_shutdown: list = []

    if startup_exception is not None:

        async def startup() -> None:
            assert startup_exception is not None  # Please mypy.
            raise startup_exception()

        on_startup.append(startup)

    if shutdown_exception is not None:

        async def shutdown() -> None:
            assert shutdown_exception is not None  # Please mypy.
            raise shutdown_exception()

        on_shutdown.append(shutdown)

    router = Router(on_startup=on_startup, on_shutdown=on_shutdown)

    # Set up spying on exchanged ASGI events.

    received_lifespan_events: typing.List[str] = []
    sent_lifespan_events: typing.List[str] = []

    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        assert scope["type"] == "lifespan"

        async def _receive() -> Message:
            message = await receive()
            received_lifespan_events.append(message["type"])
            return message

        async def _send(message: Message) -> None:
            sent_lifespan_events.append(message["type"])
            await send(message)

        await router(scope, _receive, _send)

    with contextlib.ExitStack() as stack:
        # Set up expected raised exceptions.
        if startup_exception is not None:
            stack.enter_context(pytest.raises(startup_exception))
        elif body_exception is not None:
            if shutdown_exception is not None:
                # Trio now raises the new `ExceptionGroup` in case
                # of multiple errors. (Before 3.11, this will be the backport.)
                stack.enter_context(
                    pytest.raises(
                        ExceptionGroup if concurrency == "trio" else shutdown_exception
                    )
                )
            else:
                stack.enter_context(pytest.raises(body_exception))
        elif shutdown_exception is not None:
            stack.enter_context(pytest.raises(shutdown_exception))

        async with LifespanManager(app):
            # NOTE: this block should not execute in case of startup exception.
            assert not startup_exception
            assert received_lifespan_events == ["lifespan.startup"]
            assert sent_lifespan_events == ["lifespan.startup.complete"]

            if body_exception is not None:
                raise body_exception

    # Check the log of exchanged ASGI messages in all possible cases.

    if startup_exception:
        assert received_lifespan_events == ["lifespan.startup"]
        assert sent_lifespan_events == ["lifespan.startup.failed"]
    elif body_exception:
        assert received_lifespan_events == ["lifespan.startup"]
        assert sent_lifespan_events == [
            "lifespan.startup.complete",
            "lifespan.shutdown.failed",
        ]
    elif shutdown_exception:
        assert received_lifespan_events == ["lifespan.startup", "lifespan.shutdown"]
        assert sent_lifespan_events == [
            "lifespan.startup.complete",
            "lifespan.shutdown.failed",
        ]
    else:
        assert received_lifespan_events == ["lifespan.startup", "lifespan.shutdown"]
        assert sent_lifespan_events == [
            "lifespan.startup.complete",
            "lifespan.shutdown.complete",
        ]


async def slow_startup(
    scope: dict, receive: typing.Callable, send: typing.Callable
) -> None:
    concurrency_backend = detect_concurrency_backend()
    message = await receive()
    assert message["type"] == "lifespan.startup"
    await concurrency.sleep(concurrency_backend, 0.05)
    # ...


async def slow_shutdown(
    scope: dict, receive: typing.Callable, send: typing.Callable
) -> None:
    concurrency_backend = detect_concurrency_backend()

    message = await receive()
    assert message["type"] == "lifespan.startup"
    await send({"type": "lifespan.startup.complete"})

    message = await receive()
    assert message["type"] == "lifespan.shutdown"
    await concurrency.sleep(concurrency_backend, 0.05)
    # ...


@pytest.mark.usefixtures("concurrency")
@pytest.mark.parametrize("app", [slow_startup, slow_shutdown])
async def test_lifespan_timeout(app: typing.Callable) -> None:
    with pytest.raises(TimeoutError):
        async with LifespanManager(app, startup_timeout=0.01, shutdown_timeout=0.01):
            pass


@pytest.mark.usefixtures("concurrency")
@pytest.mark.parametrize("app", [slow_startup, slow_shutdown])
async def test_lifespan_no_timeout(app: typing.Callable) -> None:
    async def main() -> None:
        async with LifespanManager(app, startup_timeout=None, shutdown_timeout=None):
            pass

    concurrency_backend = detect_concurrency_backend()
    timed_out = await concurrency.run_and_move_on_after(concurrency_backend, 0.02, main)
    assert timed_out


async def http_only(
    scope: dict, receive: typing.Callable, send: typing.Callable
) -> None:
    assert scope["type"] == "http"
    # ...


async def http_no_assert(
    scope: dict, receive: typing.Callable, send: typing.Callable
) -> None:
    await send(
        {
            "type": "http.response.start",
            "status": 200,
            "headers": [[b"content-type", b"text/plain"]],
        }
    )
    # ...


async def http_no_assert_before_receive_request(
    scope: dict, receive: typing.Callable, send: typing.Callable
) -> None:
    message = await receive()
    assert message["type"] == "http.request"
    # ...


@pytest.mark.usefixtures("concurrency")
@pytest.mark.parametrize(
    "app",
    [
        http_only,
        http_no_assert,
        pytest.param(
            http_no_assert_before_receive_request,
            marks=pytest.mark.xfail(
                reason="No way for us to detect unsupported lifespan in this case.",
                raises=AssertionError,
            ),
        ),
    ],
)
async def test_lifespan_not_supported(app: typing.Callable) -> None:
    with pytest.raises(LifespanNotSupported):
        async with LifespanManager(app):
            pass  # pragma: no cover


@pytest.mark.usefixtures("concurrency")
async def test_lifespan_state_async_cm() -> None:
    @contextlib.asynccontextmanager
    async def lifespan(_app: ASGIApp) -> typing.AsyncGenerator:
        yield {"foo": 1}

    async def get(request: Request) -> Response:
        assert request.state.foo == 1
        request.state.foo = 2
        return PlainTextResponse(f"Hello {request.state.foo}")

    app = Starlette(lifespan=lifespan, routes=[Route("/get", get)])

    async with LifespanManager(app) as manager:
        async with httpx.AsyncClient(
            app=manager.app, base_url="http://example.org"
        ) as client:
            response = await client.get("/get")
            assert response.status_code == 200
            assert response.text == "Hello 2"
