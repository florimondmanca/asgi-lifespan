import traceback
import types
import typing

T = typing.TypeVar("T")


class BaseConcurrencyBackend:
    def create_event(self) -> "BaseEvent":
        raise NotImplementedError  # pragma: no cover

    def create_queue(self, capacity: int) -> "BaseQueue":
        raise NotImplementedError  # pragma: no cover

    def create_task_group(self) -> "BaseTaskGroup":
        raise NotImplementedError  # pragma: no cover

    def finalize(self, obj: T) -> typing.AsyncContextManager[T]:
        raise NotImplementedError  # pragma: no cover

    def get_cancelled_exception_class(self) -> typing.Type[BaseException]:
        raise NotImplementedError  # pragma: no cover

    def move_on_after(
        self, seconds: typing.Optional[float]
    ) -> typing.AsyncContextManager["BaseCancelScope"]:
        raise NotImplementedError  # pragma: no cover


class BaseEvent:
    async def set(self) -> None:
        raise NotImplementedError  # pragma: no cover

    async def wait(self) -> None:
        raise NotImplementedError  # pragma: no cover


class BaseQueue:
    async def get(self) -> typing.Any:
        raise NotImplementedError  # pragma: no cover

    async def put(self, value: typing.Any) -> None:
        raise NotImplementedError  # pragma: no cover


class BaseAsyncContextManager:
    async def __aenter__(self: T) -> T:
        raise NotImplementedError  # pragma: no cover

    async def __aexit__(
        self,
        exc_type: typing.Type[BaseException] = None,
        exc_val: BaseException = None,
        exc_tb: types.TracebackType = None,
    ) -> typing.Optional[bool]:
        raise NotImplementedError  # pragma: no cover


class BaseCancelScope(BaseAsyncContextManager):
    @property
    def deadline(self) -> typing.Optional[float]:
        raise NotImplementedError  # pragma: no cover

    @property
    def timeout_expired(self) -> bool:
        raise NotImplementedError  # pragma: no cover

    async def cancel(self) -> None:
        raise NotImplementedError  # pragma: no cover


class BaseTaskGroup(BaseAsyncContextManager):
    def start_soon(
        self, func: typing.Callable[..., typing.Coroutine], *args: typing.Any
    ) -> None:
        raise NotImplementedError  # pragma: no cover


class BaseExceptionGroup(BaseException):
    """Raised when multiple exceptions have been raised in a task group."""

    SEPARATOR = "----------------------------\n"

    exceptions: typing.Sequence[BaseException]

    def __str__(self) -> str:
        tracebacks = [
            "\n".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
            for exc in self.exceptions
        ]
        return "{} exceptions were raised in the task group:\n{}{}".format(
            len(self.exceptions), self.SEPARATOR, self.SEPARATOR.join(tracebacks)
        )

    def __repr__(self) -> str:
        return "<{} ({} exceptions)>".format(
            self.__class__.__name__, len(self.exceptions)
        )
