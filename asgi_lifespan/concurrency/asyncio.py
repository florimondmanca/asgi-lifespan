import asyncio
import math
import typing
import types

from async_generator import asynccontextmanager, aclosing

from . import base

T = typing.TypeVar("T")


class AsyncioExceptionGroup(base.BaseExceptionGroup):
    def __init__(self, exceptions: typing.Sequence[BaseException]):
        super().__init__()
        self.exceptions = exceptions


class AsyncioConcurrencyBackend(base.BaseConcurrencyBackend):
    def create_event(self) -> base.BaseEvent:
        return Event()

    def create_queue(self, capacity: int) -> base.BaseQueue:
        return typing.cast(base.BaseQueue, asyncio.Queue(maxsize=capacity))

    def create_task_group(self) -> "TaskGroup":
        return TaskGroup()

    def finalize(self, obj: T) -> typing.AsyncContextManager[T]:
        return aclosing(obj)

    def get_cancelled_exception_class(self) -> typing.Type[BaseException]:
        return asyncio.CancelledError

    @asynccontextmanager
    async def move_on_after(
        self, seconds: typing.Optional[float]
    ) -> typing.AsyncIterator["CancelScope"]:
        deadline = (
            None if seconds is None else asyncio.get_running_loop().time() + seconds
        )
        async with CancelScope(deadline) as cancel_scope:
            yield cancel_scope


class Event(base.BaseEvent):
    def __init__(self) -> None:
        self._event = asyncio.Event()

    async def set(self) -> None:
        self._event.set()

    async def wait(self) -> None:
        await self._event.wait()


class CancelScope(base.BaseCancelScope):
    def __init__(self, deadline: float = None) -> None:
        self._deadline = deadline
        self._tasks: typing.Set[asyncio.Task] = set()
        self._timeout_task: typing.Optional[asyncio.Task] = None
        self._timeout_expired = False
        self._cancel_called = False
        self._active = False
        self._host_task: typing.Optional[asyncio.Task] = None

    @property
    def timeout_expired(self) -> bool:
        return self._timeout_expired

    async def __aenter__(self) -> "CancelScope":
        async def timeout() -> None:
            cancel_after = (
                math.inf
                if self._deadline is None
                else self._deadline - asyncio.get_running_loop().time()
            )
            await asyncio.sleep(cancel_after)
            self._timeout_expired = True
            await self.cancel()

        assert (
            not self._active
        ), "A CancelScope can only be used for a single 'async with' block."

        host_task = asyncio.current_task()
        assert host_task is not None
        self._host_task = host_task
        self._tasks.add(self._host_task)

        if self._deadline is not None:
            assert (
                asyncio.get_running_loop().time() < self._deadline
            ), "Negative cancel delays aren't supported yet."
            self._timeout_task = asyncio.get_running_loop().create_task(timeout())

        self._active = True

        return self

    def add(self, task: asyncio.Task) -> None:
        self._tasks.add(task)

    def remove(self, task: asyncio.Task) -> None:
        self._tasks.remove(task)

    async def flush_tasks(self) -> None:
        if not self._tasks:
            return
        done, pending = await asyncio.wait(self._tasks)
        assert not pending

    async def cancel(self) -> None:
        if self._cancel_called:
            return
        self._cancel_called = True
        await self._cancel()

    async def _cancel(self) -> None:
        # Deliver cancellation to directly contained tasks.
        # NOTE: nested cancel scopes aren't supported.
        for task in self._tasks:
            coro: typing.Coroutine = task._coro  # type: ignore
            is_running = coro.cr_await is not None
            if is_running:
                task.cancel()

    async def __aexit__(
        self,
        exc_type: typing.Type[BaseException] = None,
        exc_val: BaseException = None,
        exc_tb: types.TracebackType = None,
    ) -> typing.Optional[bool]:
        self._active = False

        if self._timeout_task:
            self._timeout_task.cancel()

        assert self._host_task is not None
        self._tasks.remove(self._host_task)

        if exc_val is not None:
            exceptions = (
                exc_val.exceptions
                if isinstance(exc_val, base.BaseExceptionGroup)
                else [exc_val]
            )

            if all(isinstance(exc, asyncio.CancelledError) for exc in exceptions):
                if self._timeout_expired:
                    return True

        return False


class TaskGroup(base.BaseTaskGroup):
    def __init__(self) -> None:
        self.cancel_scope = CancelScope()
        self._active = False
        self._exceptions: typing.List[BaseException] = []

    async def _run_wrapped_task(
        self, func: typing.Callable[..., typing.Coroutine], *args: typing.Any
    ) -> None:
        task = asyncio.current_task()
        assert task is not None
        try:
            await func(*args)
        except BaseException as exc:
            self._exceptions.append(exc)
            await self.cancel_scope.cancel()
        finally:
            self.cancel_scope.remove(task)

    def start_soon(
        self, func: typing.Callable[..., typing.Coroutine], *args: typing.Any
    ) -> None:
        assert self._active, (
            "This task group is not active - no new tasks can be spawned. "
            "To activate it, use 'async with task_group: ...'."
        )
        task = asyncio.create_task(self._run_wrapped_task(func, *args))
        self.cancel_scope.add(task)

    async def __aenter__(self) -> "TaskGroup":
        await self.cancel_scope.__aenter__()
        self._active = True
        return self

    async def __aexit__(
        self,
        exc_type: typing.Type[BaseException] = None,
        exc_val: BaseException = None,
        exc_tb: types.TracebackType = None,
    ) -> typing.Optional[bool]:
        ignore_exception = await self.cancel_scope.__aexit__(exc_type, exc_val, exc_tb)

        if exc_val is not None:
            await self.cancel_scope.cancel()
            if not ignore_exception:
                self._exceptions.append(exc_val)

        await self.cancel_scope.flush_tasks()

        self._active = False

        exceptions = [
            exc
            for exc in self._exceptions
            if not isinstance(exc, asyncio.CancelledError)
        ]

        if len(exceptions) > 1:
            raise AsyncioExceptionGroup(exceptions)
        if exceptions and exceptions[0] is not exc_val:
            raise exceptions[0]

        return ignore_exception
