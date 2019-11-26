import typing

import pytest

from asgi_lifespan.concurrency.asyncio import AsyncioBackend
from asgi_lifespan.concurrency.base import ConcurrencyBackend


@pytest.fixture(
    params=[
        pytest.param(None, marks=pytest.mark.asyncio),
        pytest.param(AsyncioBackend, marks=pytest.mark.asyncio),
    ]
)
def concurrency_backend(request: typing.Any) -> typing.Optional[ConcurrencyBackend]:
    cls = request.param
    return cls() if cls is not None else None
