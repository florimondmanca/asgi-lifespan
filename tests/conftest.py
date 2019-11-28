import pytest


@pytest.fixture(
    params=[
        pytest.param(None, marks=pytest.mark.asyncio),
        pytest.param(None, marks=pytest.mark.trio),
    ]
)
def concurrency() -> None:
    return
