"""
This module contains concurrency utilities that are only used in tests, thus not
required as part of the ConcurrencyBackend API.
"""

import asyncio
import functools
import typing

from asgi_lifespan.concurrency.asyncio import AsyncioBackend
from asgi_lifespan.concurrency.base import ConcurrencyBackend


@functools.singledispatch
async def sleep(concurrency_backend: ConcurrencyBackend, seconds: int) -> None:
    raise NotImplementedError  # pragma: no cover


async def _sleep_asyncio(concurrency_backend: ConcurrencyBackend, seconds: int) -> None:
    await asyncio.sleep(seconds)


sleep.register(None.__class__, _sleep_asyncio)
sleep.register(AsyncioBackend, _sleep_asyncio)


@functools.singledispatch
async def run_and_move_on_after(
    concurrency_backend: ConcurrencyBackend,
    seconds: typing.Optional[float],
    coroutine: typing.Callable[[], typing.Awaitable[None]],
) -> bool:
    raise NotImplementedError  # pragma: no cover


async def _run_and_move_on_after_asyncio(
    concurrency_backend: ConcurrencyBackend,
    seconds: typing.Optional[float],
    coroutine: typing.Callable[[], typing.Awaitable[None]],
) -> bool:
    try:
        await asyncio.wait_for(coroutine(), timeout=seconds)
    except asyncio.TimeoutError:
        return True
    else:
        raise NotImplementedError  # pragma: no cover


run_and_move_on_after.register(None.__class__, _run_and_move_on_after_asyncio)
run_and_move_on_after.register(AsyncioBackend, _run_and_move_on_after_asyncio)
