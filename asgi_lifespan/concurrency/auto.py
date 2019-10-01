import sniffio

from .base import BaseConcurrencyBackend


def sniff_concurrency_backend() -> BaseConcurrencyBackend:
    library = sniffio.current_async_library()
    assert library == "asyncio", f"Async library {library} is not supported yet."

    from .asyncio import AsyncioConcurrencyBackend

    return AsyncioConcurrencyBackend()
