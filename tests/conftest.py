import typing

import pytest

from asgi_lifespan.concurrency.base import BaseConcurrencyBackend
from asgi_lifespan.concurrency.asyncio import AsyncioConcurrencyBackend


@pytest.fixture(
    params=[pytest.param(AsyncioConcurrencyBackend, marks=pytest.mark.asyncio)]
)
def concurrency_backend(request: typing.Any) -> BaseConcurrencyBackend:
    cls = request.param
    return cls()
