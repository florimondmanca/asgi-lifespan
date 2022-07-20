import contextlib
import typing

import pytest
from starlette.routing import Router

from asgi_lifespan import LifespanManager, LifespanNotSupported
from asgi_lifespan._concurrency import detect_concurrency_backend
from asgi_lifespan._types import Message, Receive, Scope, Send

from . import concurrency


@pytest.mark.usefixtures("concurrency")
@pytest.mark.parametrize("startup_exception", (None, ValueError))
@pytest.mark.parametrize("body_exception", (None, ValueError))
@pytest.mark.parametrize("shutdown_exception", (None, ValueError))
async def test_lifespan_manager(
    startup_exception: typing.Optional[typing.Type[BaseException]],
    body_exception: typing.Optional[typing.Type[BaseException]],
    shutdown_exception: typing.Optional[typing.Type[BaseException]],
) -> None:
    router = Router()

    # Setup failing event handlers.

    if startup_exception is not None:

        @router.on_event("startup")
        async def startup() -> None:
            assert startup_exception is not None  # Please mypy.
            raise startup_exception

    if shutdown_exception is not None:

        @router.on_event("shutdown")
        async def shutdown() -> None:
            assert shutdown_exception is not None  # Please mypy.
            raise shutdown_exception

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
            stack.enter_context(pytest.raises(body_exception))
        elif shutdown_exception is not None:
            stack.enter_context(pytest.raises(shutdown_exception))

        async with LifespanManager(app) as ctx:
            # NOTE: this block should not execute in case of startup exception.
            assert ctx is None
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
        assert sent_lifespan_events == ["lifespan.startup.complete"]
    elif shutdown_exception:
        assert received_lifespan_events == ["lifespan.startup", "lifespan.shutdown"]
        assert sent_lifespan_events == ["lifespan.startup.complete"]
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

async def returns_without_handling_lifespan(
    scope: dict, receive: typing.Callable, send: typing.Callable
) -> None:
    if scope["type"] != "http":
        ...
        return
    raise AssertionError("Should not be called")  # pragma: no cover


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
        returns_without_handling_lifespan,
    ],
)
async def test_lifespan_not_supported(app: typing.Callable) -> None:
    with pytest.raises(LifespanNotSupported):
        async with LifespanManager(app):
            pass  # pragma: no cover
