import typing

import pytest


@pytest.fixture(
    params=[
        pytest.param("asyncio", marks=pytest.mark.asyncio),
        pytest.param("trio", marks=pytest.mark.trio),
    ]
)
def concurrency(request: typing.Any) -> str:
    return request.param
