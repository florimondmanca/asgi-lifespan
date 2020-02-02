import sys

from .base import ConcurrencyBackend


def _is_already_imported(module: str) -> bool:
    return module in sys.modules


def sniff_async_library() -> str:
    # Adapted from:
    # https://github.com/python-trio/sniffio/blob/master/sniffio/_impl.py

    if _is_already_imported("asyncio"):
        import asyncio

        try:
            current_task = asyncio.current_task
        except AttributeError:
            current_task = asyncio.Task.current_task

        try:
            task = current_task()
        except RuntimeError:
            pass
        else:
            if task is not None:
                return "asyncio"

    if _is_already_imported("trio"):
        import trio

        try:
            task = trio.hazmat.current_task()
        except RuntimeError:
            pass
        else:
            assert task is not None
            return "trio"

    raise NotImplementedError(
        "Unknown async library, or not in async context."
    )  # pragma: no cover


def detect_concurrency_backend() -> ConcurrencyBackend:
    library = sniff_async_library()
    assert library in ("asyncio", "trio")

    if library == "trio":
        from .trio import TrioBackend

        return TrioBackend()
    else:
        from .asyncio import AsyncioBackend

        return AsyncioBackend()
