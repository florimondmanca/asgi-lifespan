import typing

import pytest

from asgi_lifespan import LifespanContext, LifespanNotSupported

from .compat import nullcontext
from .utils import MockLifespan, hello_world


class FakeAppException(Exception):
    pass


@pytest.mark.anyio
async def test_lifespan_not_supported() -> None:
    with pytest.raises(LifespanNotSupported):
        async with LifespanContext(app=hello_world):
            pass  # pragma: no cover


@pytest.mark.anyio
@pytest.mark.parametrize("handle_startup_failed", (True, False))
@pytest.mark.parametrize("startup_exception", (None, FakeAppException))
async def test_asgi_lifespan(
    scope: dict,
    receive: typing.Callable,
    send: typing.Callable,
    *,
    startup_exception: typing.Optional[typing.Type[BaseException]],
    handle_startup_failed: bool,
) -> None:
    app = MockLifespan(
        app=hello_world,
        startup_exception=startup_exception,
        handle_startup_failed=handle_startup_failed,
    )

    with pytest.raises(FakeAppException) if startup_exception else nullcontext():
        async with LifespanContext(app=app) as ctx:
            assert ctx is None

            # Inspect ASGI events exchanged during the startup phase.
            assert "lifespan.startup" in app.received_lifespan_events

            startup_event = (
                f"lifespan.startup.{'failed' if startup_exception else 'complete'}"
            )
            if not startup_exception or handle_startup_failed:
                assert startup_event in app.sent_lifespan_events

            await app(scope, receive, send)

    # Inspect ASGI events exchanged during the shutdown phase, if it happened.
    if startup_exception:
        assert "lifespan.shutdown" not in app.received_lifespan_events
    else:
        assert "lifespan.shutdown" in app.received_lifespan_events
        assert "lifespan.shutdown.complete" in app.sent_lifespan_events
