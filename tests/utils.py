import typing


async def hello_world(
    scope: dict, receive: typing.Callable, send: typing.Callable
) -> None:
    assert scope["type"] == "http"
    status = 200
    output = b"Hello, World!"
    headers = [(b"content-type", "text/plain"), (b"content-length", str(len(output)))]

    await send({"type": "http.response.start", "status": status, "headers": headers})
    await send({"type": "http.response.body", "body": output})


class MockLifespan:
    """Add lifespan support to an ASGI app, and record exchanged lifespan events."""

    def __init__(
        self,
        app: typing.Callable,
        startup_exception: typing.Type[BaseException] = None,
        handle_startup_failed: bool = False,
    ):
        self.app = app
        self.received_lifespan_events: typing.List[str] = []
        self.sent_lifespan_events: typing.List[str] = []
        self.startup_exception = startup_exception
        self.handle_startup_failed = handle_startup_failed

    async def startup(self) -> None:
        if self.startup_exception is not None:
            raise self.startup_exception

    async def __call__(
        self, scope: dict, receive: typing.Callable, send: typing.Callable
    ) -> None:
        if scope["type"] != "lifespan":
            await self.app(scope, receive, send)
            return

        async def _receive() -> dict:
            message = await receive()
            self.received_lifespan_events.append(message["type"])
            return message

        async def _send(message: dict) -> None:
            self.sent_lifespan_events.append(message["type"])
            await send(message)

        message = await _receive()
        assert message["type"] == "lifespan.startup", message["type"]

        try:
            await self.startup()
        except BaseException:
            if self.handle_startup_failed:
                await _send({"type": "lifespan.startup.failed"})
            raise
        else:
            await _send({"type": "lifespan.startup.complete"})

        message = await _receive()
        assert message["type"] == "lifespan.shutdown", message["type"]
        await _send({"type": "lifespan.shutdown.complete"})
