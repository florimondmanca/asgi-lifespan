import inspect
import typing
from types import TracebackType

import anyio

from .compat import AsyncExitStack, asynccontextmanager
from .exceptions import LifespanNotSupported


class LifespanManager:
    def __init__(
        self,
        app: typing.Callable,
        startup_timeout: typing.Optional[float] = 5,
        shutdown_timeout: typing.Optional[float] = 5,
    ) -> None:
        self.app = app
        self.startup_timeout = startup_timeout
        self.shutdown_timeout = shutdown_timeout
        self._exit_stack = AsyncExitStack()

    async def __aenter__(self) -> None:
        await self._exit_stack.__aenter__()

        agen = _lifespan_manager_generator(
            self.app,
            startup_timeout=self.startup_timeout,
            shutdown_timeout=self.shutdown_timeout,
        )

        # Ensure the async generator used by @asynccontextmanager is properly
        # closed on exit by wrapping it in anyio.finalize().
        # This prevents a warning raised by curio in particular.
        agen = await self._exit_stack.enter_async_context(anyio.finalize(agen))
        assert inspect.isasyncgen(agen)

        @asynccontextmanager
        async def get_context() -> typing.AsyncIterator[None]:
            # This could have been a regular function returning `agen`, but on 3.6 we
            # use `async_generator.asynccontextmanager`. It expects the function it is
            # given to be a proper async generator function, hence this wrapper.
            async for _ in agen:
                yield

        await self._exit_stack.enter_async_context(get_context())

    async def __aexit__(
        self,
        exc_type: typing.Type[BaseException] = None,
        exc_value: BaseException = None,
        traceback: TracebackType = None,
    ) -> typing.Optional[bool]:
        return await self._exit_stack.__aexit__(exc_type, exc_value, traceback)


async def _lifespan_manager_generator(
    app: typing.Callable,
    startup_timeout: typing.Optional[float],
    shutdown_timeout: typing.Optional[float],
) -> typing.AsyncIterator[None]:
    startup_complete = anyio.create_event()
    shutdown_complete = anyio.create_event()

    scope = {"type": "lifespan"}
    receive_queue = anyio.create_queue(capacity=1)
    receive_called = False

    async def receive() -> dict:
        nonlocal receive_called
        receive_called = True
        return await receive_queue.get()

    async def send(message: dict) -> None:
        if not receive_called:
            raise LifespanNotSupported(
                "Application called send() before receive(). "
                "Is it missing `assert scope['type'] == 'http'` or similar?"
            )

        if message["type"] == "lifespan.startup.complete":
            await startup_complete.set()
        elif message["type"] == "lifespan.shutdown.complete":
            await shutdown_complete.set()

    async def run_app() -> None:
        try:
            await app(scope, receive, send)
        except Exception as exc:
            if isinstance(exc, anyio.get_cancelled_exc_class()):
                # Stay out of the way of task cancellation.
                raise
            if not receive_called:
                raise LifespanNotSupported(
                    "Application failed before making its first call to 'receive()'. "
                    "We expect this to originate from a statement similar to "
                    "`assert scope['type'] == 'type'`. "
                    "If that is not the case, then this crash is unexpected and "
                    "there is probably more debug output in the cause traceback."
                ) from exc
            raise

    async with anyio.create_task_group() as group:
        await group.spawn(run_app)

        await receive_queue.put({"type": "lifespan.startup"})
        async with anyio.fail_after(startup_timeout):
            await startup_complete.wait()

        yield

        await receive_queue.put({"type": "lifespan.shutdown"})
        async with anyio.fail_after(shutdown_timeout):
            await shutdown_complete.wait()
