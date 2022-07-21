"""
This module contains concurrency utilities that are only used in tests, thus not
required as part of the ConcurrencyBackend API.
"""

import asyncio
import functools
import typing

import trio

from asgi_lifespan._concurrency.asyncio import AsyncioBackend
from asgi_lifespan._concurrency.base import ConcurrencyBackend
from asgi_lifespan._concurrency.trio import TrioBackend


@functools.singledispatch
async def sleep(concurrency_backend: ConcurrencyBackend, seconds: float) -> None:
    raise NotImplementedError  # pragma: no cover


@sleep.register(AsyncioBackend)
async def _sleep_asyncio(
    concurrency_backend: ConcurrencyBackend, seconds: float
) -> None:
    await asyncio.sleep(seconds)


@sleep.register(TrioBackend)
async def _sleep_trio(concurrency_backend: ConcurrencyBackend, seconds: float) -> None:
    await trio.sleep(seconds)


@functools.singledispatch
async def run_and_move_on_after(
    concurrency_backend: ConcurrencyBackend,
    seconds: typing.Optional[float],
    coroutine: typing.Callable[[], typing.Awaitable[None]],
) -> bool:
    raise NotImplementedError  # pragma: no cover


@run_and_move_on_after.register(AsyncioBackend)
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


@run_and_move_on_after.register(TrioBackend)
async def _run_and_move_on_after_trio(
    concurrency_backend: ConcurrencyBackend,
    seconds: typing.Optional[float],
    coroutine: typing.Callable[[], typing.Awaitable[None]],
) -> bool:
    with trio.move_on_after(seconds if seconds is not None else float("inf")):
        await coroutine()
        raise NotImplementedError  # pragma: no cover
    return True
