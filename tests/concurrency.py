import asyncio
import functools

from asgi_lifespan.concurrency.base import BaseConcurrencyBackend
from asgi_lifespan.concurrency.asyncio import AsyncioConcurrencyBackend


@functools.singledispatch
async def sleep(concurrency_backend: BaseConcurrencyBackend, seconds: int) -> None:
    raise NotImplementedError  # pragma: no cover


@sleep.register(AsyncioConcurrencyBackend)
async def _sleep_asyncio(
    concurrency_backend: AsyncioConcurrencyBackend, seconds: int
) -> None:
    await asyncio.sleep(seconds)
