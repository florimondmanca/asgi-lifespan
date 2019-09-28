import contextlib
import typing

import pytest

from asgi_lifespan import Lifespan

Log = typing.List[typing.Union[str, dict]]


def build_lifespan(log: Log, startup_failed: bool) -> typing.Callable:
    lifespan = Lifespan(
        on_startup=lambda: log.append("sync startup"),
        on_shutdown=lambda: log.append("sync shutdown"),
    )

    @lifespan.on_event("startup")
    async def startup() -> None:
        log.append("startup")

    @lifespan.on_event("shutdown")
    async def shutdown() -> None:
        log.append("shutdown")

    async def more_startup() -> None:
        log.append("more startup")

    async def more_shutdown() -> None:
        log.append("more shutdown")

    lifespan.add_event_handler("startup", more_startup)
    lifespan.add_event_handler("shutdown", more_shutdown)

    if startup_failed:

        @lifespan.on_event("startup")
        async def failing_startup() -> None:
            raise RuntimeError

    return lifespan


def build_asgi_arguments(
    log: Log, messages: list
) -> typing.Tuple[dict, typing.Callable, typing.Callable]:
    scope = {"type": "lifespan"}

    async def receive() -> dict:
        message = messages.pop()
        log.append({"type": message["type"]})
        return message

    async def send(message: dict) -> None:
        log.append({"type": message["type"]})

    return scope, receive, send


@pytest.mark.anyio
@pytest.mark.parametrize("startup_failed", (False, True))
async def test_lifespan_app(startup_failed: bool,) -> None:
    log: Log = []
    messages = [{"type": "lifespan.shutdown"}, {"type": "lifespan.startup"}]

    lifespan = build_lifespan(log=log, startup_failed=startup_failed)
    scope, receive, send = build_asgi_arguments(log=log, messages=messages)

    with contextlib.ExitStack() as stack:
        if startup_failed:
            stack.enter_context(pytest.raises(RuntimeError))
        await lifespan(scope, receive, send)

    if startup_failed:
        assert messages == [{"type": "lifespan.shutdown"}]
        assert log == [
            {"type": "lifespan.startup"},
            "sync startup",
            "startup",
            "more startup",
            {"type": "lifespan.startup.failed"},
        ]
    else:
        assert messages == []
        assert log == [
            {"type": "lifespan.startup"},
            "sync startup",
            "startup",
            "more startup",
            {"type": "lifespan.startup.complete"},
            {"type": "lifespan.shutdown"},
            "sync shutdown",
            "shutdown",
            "more shutdown",
            {"type": "lifespan.shutdown.complete"},
        ]
