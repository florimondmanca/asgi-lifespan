import inspect
import typing
from types import TracebackType

from ._concurrency import ConcurrencyBackend, detect_concurrency_backend
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
        self.concurrency_backend = detect_concurrency_backend()
        self.startup_timeout = startup_timeout
        self.shutdown_timeout = shutdown_timeout
        self._exit_stack = AsyncExitStack()

    async def __aenter__(self) -> None:
        await self._exit_stack.__aenter__()

        agen = _lifespan_manager_generator(
            self.app,
            startup_timeout=self.startup_timeout,
            shutdown_timeout=self.shutdown_timeout,
            concurrency_backend=self.concurrency_backend,
        )

        # Ensure the async generator used by @asynccontextmanager is properly
        # closed on exit, even in case of an exception.
        agen = await self._exit_stack.enter_async_context(
            self.concurrency_backend.finalize(agen)
        )
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
    concurrency_backend: ConcurrencyBackend,
) -> typing.AsyncGenerator[None, None]:
    startup_complete = concurrency_backend.create_event()
    shutdown_complete = concurrency_backend.create_event()

    scope = {"type": "lifespan"}
    receive_queue = concurrency_backend.create_queue(capacity=2)
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
            startup_complete.set()
        elif message["type"] == "lifespan.shutdown.complete":
            shutdown_complete.set()

    async def run_app() -> None:
        try:
            await app(scope, receive, send)
        except Exception as exc:
            # If the app crashed, we should abort startup and shutdown as soon
            # as possible, instead of waiting until timeout.
            startup_complete.set()
            shutdown_complete.set()

            if not receive_called:
                raise LifespanNotSupported(
                    "Application failed before making its first call to 'receive()'. "
                    "We expect this to originate from a statement similar to "
                    "`assert scope['type'] == 'type'`. "
                    "If that is not the case, then this crash is unexpected and "
                    "there is probably more debug output in the cause traceback."
                ) from exc

            raise

    async with concurrency_backend.run_in_background(run_app):
        await receive_queue.put({"type": "lifespan.startup"})
        await concurrency_backend.run_and_fail_after(
            startup_timeout, startup_complete.wait
        )
        yield
        await receive_queue.put({"type": "lifespan.shutdown"})
        await concurrency_backend.run_and_fail_after(
            shutdown_timeout, shutdown_complete.wait
        )
