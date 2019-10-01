import inspect
import typing
from types import TracebackType

from .concurrency.auto import sniff_concurrency_backend
from .concurrency.base import BaseConcurrencyBackend

from .compat import AsyncExitStack, asynccontextmanager
from .exceptions import LifespanNotSupported


class LifespanManager:
    def __init__(
        self,
        app: typing.Callable,
        startup_timeout: typing.Optional[float] = 5,
        shutdown_timeout: typing.Optional[float] = 5,
        concurrency_backend: BaseConcurrencyBackend = None,
    ) -> None:
        if concurrency_backend is None:
            concurrency_backend = sniff_concurrency_backend()
        self.app = app
        self.startup_timeout = startup_timeout
        self.shutdown_timeout = shutdown_timeout
        self.concurrency_backend = concurrency_backend
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
        # closed on exit by wrapping it in 'finalize()'.
        # This prevents a warning raised by curio in particular.
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
    concurrency_backend: BaseConcurrencyBackend,
) -> typing.AsyncIterator[None]:
    startup_complete = concurrency_backend.create_event()
    shutdown_complete = concurrency_backend.create_event()

    scope = {"type": "lifespan"}
    receive_queue = concurrency_backend.create_queue(capacity=1)
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
            if isinstance(exc, concurrency_backend.get_cancelled_exception_class()):
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

    async with concurrency_backend.create_task_group() as group:
        group.start_soon(run_app)

        await receive_queue.put({"type": "lifespan.startup"})
        async with concurrency_backend.move_on_after(startup_timeout) as cancel_scope:
            await startup_complete.wait()
        if cancel_scope.timeout_expired:
            raise TimeoutError

        yield

        await receive_queue.put({"type": "lifespan.shutdown"})
        async with concurrency_backend.move_on_after(shutdown_timeout) as cancel_scope:
            await shutdown_complete.wait()
        if cancel_scope.timeout_expired:
            raise TimeoutError
