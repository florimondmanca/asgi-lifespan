from .asyncio import AsyncioBackend
from .base import ConcurrencyBackend


def get_default_concurrency_backend() -> ConcurrencyBackend:
    return AsyncioBackend()
