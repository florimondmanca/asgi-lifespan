import typing

AsyncEventHandler = typing.Callable[[], typing.Awaitable[None]]
SyncEventHandler = typing.Callable[[], None]
E = typing.TypeVar("E", AsyncEventHandler, SyncEventHandler)

# ASGI types.
# Copied from: https://github.com/encode/starlette/blob/master/starlette/types.py
Scope = typing.MutableMapping[str, typing.Any]
Message = typing.MutableMapping[str, typing.Any]
Receive = typing.Callable[[], typing.Awaitable[Message]]
Send = typing.Callable[[Message], typing.Awaitable[None]]
ASGIApp = typing.Callable[[Scope, Receive, Send], typing.Awaitable[None]]
