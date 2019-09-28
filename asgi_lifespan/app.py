import inspect
import traceback
import typing


class Lifespan:
    def __init__(
        self, on_startup: typing.Callable = None, on_shutdown: typing.Callable = None
    ) -> None:
        self.startup_handlers = [] if on_startup is None else [on_startup]
        self.shutdown_handlers = [] if on_shutdown is None else [on_shutdown]

    def add_event_handler(self, event_type: str, func: typing.Callable) -> None:
        assert event_type in {"startup", "shutdown"}

        if event_type == "startup":
            self.startup_handlers.append(func)
        else:
            assert event_type == "shutdown"
            self.shutdown_handlers.append(func)

    def on_event(self, event_type: str) -> typing.Callable:
        def decorate(func: typing.Callable) -> typing.Callable:
            self.add_event_handler(event_type, func)
            return func

        return decorate

    async def startup(self) -> None:
        for handler in self.startup_handlers:
            if inspect.iscoroutinefunction(handler):
                await handler()
            else:
                handler()

    async def shutdown(self) -> None:
        for handler in self.shutdown_handlers:
            if inspect.iscoroutinefunction(handler):
                await handler()
            else:
                handler()

    async def __call__(
        self, scope: dict, receive: typing.Callable, send: typing.Callable
    ) -> None:
        message = await receive()
        assert message["type"] == "lifespan.startup"

        try:
            await self.startup()
        except BaseException:
            message = traceback.format_exc()
            await send({"type": "lifespan.startup.failed", "message": message})
            raise

        await send({"type": "lifespan.startup.complete"})

        message = await receive()
        assert message["type"] == "lifespan.shutdown"
        await self.shutdown()
        await send({"type": "lifespan.shutdown.complete"})
