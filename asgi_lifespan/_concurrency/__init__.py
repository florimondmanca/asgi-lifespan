from .base import ConcurrencyBackend


def detect_concurrency_backend() -> ConcurrencyBackend:
    from .asyncio import AsyncioBackend

    try:
        import sniffio
    except ImportError:  # pragma: no cover
        # sniffio would have been installed with trio,
        # so we must be running on asyncio.
        return AsyncioBackend()

    library = sniffio.current_async_library()
    assert library in ("asyncio", "trio")

    if library == "asyncio":
        return AsyncioBackend()

    from .trio import TrioBackend

    return TrioBackend()
