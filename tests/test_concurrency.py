import pytest

from asgi_lifespan.concurrency.asyncio import (
    AsyncioConcurrencyBackend,
    AsyncioExceptionGroup,
)


@pytest.mark.asyncio
async def test_task_group_multiple_exceptions() -> None:
    backend = AsyncioConcurrencyBackend()

    async def task1() -> None:
        raise RuntimeError("Oops 1")

    async def task2() -> None:
        raise RuntimeError("Oops 2")

    with pytest.raises(AsyncioExceptionGroup) as ctx:
        async with backend.create_task_group() as task_group:
            task_group.start_soon(task1)
            task_group.start_soon(task2)

    assert repr(ctx.value) == "<AsyncioExceptionGroup (2 exceptions)>"
    assert [str(exc) for exc in ctx.value.exceptions] == ["Oops 1", "Oops 2"]
    assert "Oops 1" in str(ctx.value)
    assert "Oops 2" in str(ctx.value)
