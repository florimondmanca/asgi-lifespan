# asgi-lifespan

[![Build Status](https://travis-ci.com/florimondmanca/asgi-lifespan.svg?branch=master)](https://travis-ci.com/florimondmanca/asgi-lifespan)
[![Coverage](https://codecov.io/gh/florimondmanca/asgi-lifespan/branch/master/graph/badge.svg)](https://codecov.io/gh/florimondmanca/asgi-lifespan)
[![Package version](https://badge.fury.io/py/asgi-lifespan.svg)](https://pypi.org/project/asgi-lifespan)

[Lifespan protocol](https://asgi.readthedocs.io/en/latest/specs/lifespan.html) support for ASGI apps and libraries.

## Features

- Add lifespan event handlers to an ASGI app using `LifespanMiddleware` (_TODO_).
- Send lifespan events to an ASGI app using `LifespanManager` (_TODO_).
- Support for [asyncio], [trio] and [curio] (provided by [anyio]).
- Fully type-annotated.
- 100% test coverage.

[asyncio]: https://docs.python.org/3/library/asyncio
[trio]: https://anyio.readthedocs.io/en/latest/
[curio]: https://anyio.readthedocs.io/en/latest/
[anyio]: https://anyio.readthedocs.io

## Quickstart

```python
from asgi_lifespan import LifespanManager, LifespanMiddleware

from myproject.asgi import app

app = LifespanMiddleware(app)

@app.on_event("startup")
async def startup():
    print("Starting up...")

@app.on_event("shutdown")
async def shutdown():
    print("Shutting down...")

async def main():
    async with LifespanManager(app):
        print("We're in!")
```

To run this example, use any of the supported async libraries:

```python
import asyncio
asyncio.run(main())

import trio
trio.run(main)

import curio
curio.run(main)
```

If you save the file as `main.py` and run `$ python main.py`, you will get the following output:

```console
Starting up...
We're in!
Shutting down...
```

## Installation

Soon available on PyPI.

## License

MIT
