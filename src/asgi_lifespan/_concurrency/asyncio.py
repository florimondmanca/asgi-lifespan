import asyncio
import contextlib
from types import TracebackType
from typing import Any, AsyncContextManager, Awaitable, Callable, Type

from .base import BaseEvent, BaseQueue, ConcurrencyBackend


class AsyncioEvent(BaseEvent):
    def __init__(self) -> None:
        self._event = asyncio.Event()

    def set(self) -> None:
        self._event.set()

    async def wait(self) -> None:
        await self._event.wait()


class AsyncioQueue(BaseQueue):
    def __init__(self, capacity: int) -> None:
        self._queue: asyncio.Queue[Any] = asyncio.Queue(maxsize=capacity)

    async def get(self) -> Any:
        return await self._queue.get()

    async def put(self, value: Any) -> None:
        await self._queue.put(value)


class AsyncioBackend(ConcurrencyBackend):
    def create_event(self) -> BaseEvent:
        return AsyncioEvent()

    def create_queue(self, capacity: int) -> BaseQueue:
        return AsyncioQueue(capacity=capacity)

    async def run_and_fail_after(
        self,
        seconds: float | None,
        coroutine: Callable[[], Awaitable[None]],
    ) -> None:
        try:
            await asyncio.wait_for(coroutine(), timeout=seconds)
        except asyncio.TimeoutError:
            raise TimeoutError

    def run_in_background(
        self, coroutine: Callable[[], Awaitable[None]]
    ) -> AsyncContextManager:
        return Background(coroutine)


class Background:
    def __init__(self, coroutine: Callable[[], Awaitable[None]]) -> None:
        self.coroutine = coroutine
        self.task: asyncio.Task | None = None
        self._task_exception: BaseException | None = None

    async def __aenter__(self) -> None:
        async def run_and_silence_cancelled() -> None:
            with contextlib.suppress(asyncio.CancelledError):
                await self.coroutine()

        loop = asyncio.get_event_loop()
        self.task = loop.create_task(run_and_silence_cancelled())

    async def __aexit__(
        self,
        exc_type: Type[BaseException] | None = None,
        exc_value: BaseException | None = None,
        traceback: TracebackType | None = None,
    ) -> None:
        assert self.task is not None

        _, pending = await asyncio.wait({self.task}, timeout=0)
        if pending:
            self.task.cancel()

        await self.task

        if exc_type is None:
            self.task.result()
