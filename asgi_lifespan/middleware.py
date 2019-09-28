import typing


class LifespanMiddleware:
    def __init__(self, app: typing.Callable, lifespan: typing.Callable) -> None:
        self.app = app
        self.lifespan = lifespan

    async def __call__(
        self, scope: dict, receive: typing.Callable, send: typing.Callable
    ) -> None:
        if scope["type"] == "lifespan":
            await self.lifespan(scope, receive, send)
        else:
            await self.app(scope, receive, send)
