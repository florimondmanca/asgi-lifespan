# asgi-lifespan

[![Build Status](https://travis-ci.com/florimondmanca/asgi-lifespan.svg?branch=master)](https://travis-ci.com/florimondmanca/asgi-lifespan)
[![Coverage](https://codecov.io/gh/florimondmanca/asgi-lifespan/branch/master/graph/badge.svg)](https://codecov.io/gh/florimondmanca/asgi-lifespan)
[![Package version](https://badge.fury.io/py/asgi-lifespan.svg)](https://pypi.org/project/asgi-lifespan)

Modular components for adding [lifespan protocol](https://asgi.readthedocs.io/en/latest/specs/lifespan.html) support to [ASGI] apps and libraries.

[asgi]: https://asgi.readthedocs.io

**Contents**

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
  - [Adding lifespan to ASGI apps](#adding-lifespan-to-asgi-apps)
  - [Sending lifespan events](#sending-lifespan-events)
- [API Reference](#api-reference)
  - [`Lifespan`](#lifespan)

## Features

- Create a lifespan-capable ASGI app with event handler registration support using `Lifespan`.
- Add lifespan support to an ASGI app using `LifespanMiddleware`.
- Send lifespan events to an ASGI app (e.g. for testing) using `LifespanManager`. (_TODO_)
- Support for [asyncio], [trio] and [curio] (provided by [anyio]).
- Fully type-annotated.
- 100% test coverage.

[asyncio]: https://docs.python.org/3/library/asyncio
[trio]: https://anyio.readthedocs.io/en/latest/
[curio]: https://anyio.readthedocs.io/en/latest/
[anyio]: https://anyio.readthedocs.io

## Installation

```bash
pip install asgi-lifespan
```

## Usage

### Adding lifespan to ASGI apps

```python
from asgi_lifespan import Lifespan, LifespanMiddleware


# 'Lifespan' is a standalone ASGI app.
# It implements the lifespan protocol,
# and allows registering lifespan event handlers.

lifespan = Lifespan()


@lifespan.on_event("startup")
async def startup():
    print("Starting up...")


@lifespan.on_event("shutdown")
async def shutdown():
    print("Shutting down...")


# Sync event handlers and an imperative syntax are supported too.


def more_shutdown():
    print("Bye!")


lifespan.add_event_handler("shutdown", more_shutdown)


# Example ASGI app. We're using a "Hello, world" application here,
# but any ASGI-compliant callable will do.

async def app(scope, receive, send):
    assert scope["type"] == "http"
    output = b"Hello, World!"
    headers = [
        (b"content-type", "text/plain"),
        (b"content-length", str(len(output)))
    ]
    await send(
        {"type": "http.response.start", "status": 200, "headers": headers}
    )
    await send({"type": "http.response.body", "body": output})


# 'LifespanMiddleware' returns an ASGI app.
# It forwards lifespan requests to 'lifespan',
# and anything else goes to 'app'.

app = LifespanMiddleware(app, lifespan=lifespan)
```

Save this script as `app.py`. You can serve this application with an ASGI server such as [uvicorn]:

[uvicorn]: https://www.uvicorn.org/

```bash
uvicorn app:app
```

You should get the following output:

```console
INFO: Started server process [2407]
INFO: Waiting for application startup.
Starting up...
INFO: Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

Stop the server using `Ctrl+C`, and you should get the following output:

```console
INFO: Shutting down
INFO: Waiting for application shutdown.
Shutting down...
Bye!
INFO: Finished server process [2407]
```

### Sending lifespan events

To programmatically send ASGI lifespan events to an ASGI app, use `LifespanManager`. This is particularly useful for testing and/or making requests using an ASGI-capable HTTP client such as [HTTPX].

[httpx]: https://www.encode.io/httpx/

```python
from asgi_lifespan import Lifespan, LifespanManager


# Example lifespan-capable ASGI app.
# (Doesn't need to be a `Lifespan` instance.
# Any ASGI app implementing the lifespan protocol will do.)

app = Lifespan()


@app.on_event("startup")
async def startup():
    print("Starting up...")


@app.on_event("shutdown")
async def shutdown():
    print("Shutting down...")


async def main():
    async with LifespanManager(app):
        print("We're in!")
        # Maybe make some requests to 'app'
        # using an ASGI-capable test client here?
```

> **Note**: if `LifespanManager` detects that the lifespan protocol isn't supported, a `LifespanNotSupported` exception is raised. To silence this exception, use `LifespanManager(app, ignore_unsupported=True)`.

Save this script as `main.py`. You can run it with any of the supported async libraries:

```python
# Add one of these at the bottom of 'main.py'.

import asyncio
asyncio.run(main())

import trio
trio.run(main)

import curio
curio.run(main)
```

Run `$ python main.py` in your terminal, and you should get the following output:

```console
Starting up...
We're in!
Shutting down...
```

## API Reference

### `Lifespan`

```python
def __init__(self, on_startup: Callable = None, on_shutdown: Callable = None)
```

A standalone ASGI app that implements the lifespan protocol and supports registering event handlers.

**Example**

```python
lifespan = Lifespan()
```

**Parameters**

- `on_startup` (`Callable`): an optional initial startup event handler.
- `on_shutdown` (`Callable`): an optional initial shutdown event handler.

#### `add_event_handler`

```python
def add_event_handler(self, event_type: str, func: Callable[[], None]) -> None
```

Register a callback to be called when the application starts up or shuts down.

Imperative version of [`.on_event()`](#on_event).

**Example**

```python
async def on_startup():
    ...

lifespan.add_event_handler("startup", on_startup)
```

**Parameters**

- `event_type` (`str`): one of `"startup"` or `"shutdown"`.
- `func` (`Callable`): a callback. Can be sync or async.

#### `on_event`

```python
def on_event(self, event_type: str) -> Callable[[], None]
```

Register a callback to be called when the application starts up or shuts down.

Decorator version of [`.add_event_handler()`](#add_event_handler).

**Example**

```python
@lifespan.on_event("startup")
async def on_startup():
    ...
```

**Parameters**

- `event_type` (`str`): one of `"startup"` or `"shutdown"`.

#### `__call__`

```python
async def __call__(self, scope: dict, receive: Callable, send: Callable) -> None
```

ASGI 3 implementation.

## License

MIT
