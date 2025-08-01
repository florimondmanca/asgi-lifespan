import pytest

from typing import Any


@pytest.fixture(
    params=[
        pytest.param("asyncio", marks=pytest.mark.asyncio),
        pytest.param("trio", marks=pytest.mark.trio),
    ]
)
def concurrency(request: Any) -> str:
    return request.param
