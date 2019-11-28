import typing


class BaseEvent:
    def set(self) -> None:
        raise NotImplementedError  # pragma: no cover

    async def wait(self) -> None:
        raise NotImplementedError  # pragma: no cover


class BaseQueue:
    async def get(self) -> typing.Any:
        raise NotImplementedError  # pragma: no cover

    async def put(self, value: typing.Any) -> None:
        raise NotImplementedError  # pragma: no cover


class ConcurrencyBackend:
    def create_event(self) -> BaseEvent:
        raise NotImplementedError  # pragma: no cover

    def create_queue(self, capacity: int) -> BaseQueue:
        raise NotImplementedError  # pragma: no cover

    async def run_and_fail_after(
        self,
        seconds: typing.Optional[float],
        coroutine: typing.Callable[[], typing.Awaitable[None]],
    ) -> None:
        raise NotImplementedError  # pragma: no cover

    def finalize(
        self, agen: typing.AsyncGenerator[None, None]
    ) -> typing.AsyncContextManager:
        return Finalize(agen)

    def run_in_background(
        self, coroutine: typing.Callable[[], typing.Awaitable[None]]
    ) -> typing.AsyncContextManager:
        raise NotImplementedError  # pragma: no cover


class Finalize:
    def __init__(self, agen: typing.AsyncGenerator):
        self._agen = agen

    async def __aenter__(self) -> typing.AsyncGenerator:
        return self._agen

    async def __aexit__(self, *args: typing.Any) -> None:
        await self._agen.aclose()
