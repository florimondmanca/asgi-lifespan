from collections.abc import Awaitable, MutableMapping
from typing import Any, Callable

# ASGI types.
# Copied from: https://github.com/encode/starlette/blob/master/starlette/types.py
Scope = MutableMapping[str, Any]
Message = MutableMapping[str, Any]

Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]

ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]
