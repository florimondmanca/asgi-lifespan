try:
    from contextlib import asynccontextmanager
except ImportError:  # pragma: no cover
    from async_generator import asynccontextmanager  # type: ignore # noqa: F401

try:
    from contextlib import AsyncExitStack
except ImportError:  # pragma: no cover
    from async_exit_stack import AsyncExitStack  # type: ignore # noqa: F401
