import inspect
import traceback
import typing

from ._types import AsyncEventHandler, E, Receive, Scope, Send, SyncEventHandler


class Lifespan:
    def __init__(
        self,
        on_startup: typing.Union[AsyncEventHandler, SyncEventHandler] = None,
        on_shutdown: typing.Union[AsyncEventHandler, SyncEventHandler] = None,
    ) -> None:
        self.startup_handlers = [] if on_startup is None else [on_startup]
        self.shutdown_handlers = [] if on_shutdown is None else [on_shutdown]

    def add_event_handler(self, event_type: str, func: E) -> None:
        assert event_type in {"startup", "shutdown"}

        if event_type == "startup":
            self.startup_handlers.append(func)
        else:
            assert event_type == "shutdown"
            self.shutdown_handlers.append(func)

    def on_event(self, event_type: str) -> typing.Callable[[E], E]:
        def decorate(func: E) -> E:
            self.add_event_handler(event_type, func)
            return func

        return decorate

    async def startup(self) -> None:
        for handler in self.startup_handlers:
            value = handler()
            if value is None:
                continue
            assert inspect.iscoroutine(value)
            await value

    async def shutdown(self) -> None:
        for handler in self.shutdown_handlers:
            value = handler()
            if value is None:
                continue
            assert inspect.iscoroutine(value)
            await value

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        message = await receive()
        assert message["type"] == "lifespan.startup"

        try:
            await self.startup()
        except BaseException:
            msg = traceback.format_exc()
            await send({"type": "lifespan.startup.failed", "message": msg})
            raise

        await send({"type": "lifespan.startup.complete"})

        message = await receive()
        assert message["type"] == "lifespan.shutdown"
        await self.shutdown()
        await send({"type": "lifespan.shutdown.complete"})
