import typing

import pytest


@pytest.fixture
def scope() -> dict:
    return {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "headers": [
            (b"host", b"testserver"),
            (b"user-agent", b"python-httpx/0.7.4"),
            (b"accept", b"*/*"),
            (b"accept-encoding", b"gzip, deflate, br"),
            (b"connection", b"keep-alive"),
        ],
        "scheme": "http",
        "path": "/",
        "query_string": b"",
        "server": "test",
        "client": ("testserver", 4321),
        "root_path": "",
    }


@pytest.fixture
def receive() -> typing.Callable:
    async def mock_receive() -> dict:
        raise NotImplementedError  # pragma: no cover

    return mock_receive


@pytest.fixture
def send() -> typing.Callable:
    async def mock_send(message: dict) -> None:
        pass

    return mock_send
