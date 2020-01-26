from ._types import ASGIApp, Receive, Scope, Send


class LifespanMiddleware:
    def __init__(self, app: ASGIApp, lifespan: ASGIApp) -> None:
        self.app = app
        self.lifespan = lifespan

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "lifespan":
            await self.lifespan(scope, receive, send)
        else:
            await self.app(scope, receive, send)
