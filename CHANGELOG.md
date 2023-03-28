# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## 2.1.0 - 2023-03-28

### Added

- Add support for lifespan state. (Pull #59)

## 2.0.0 - 2022-11-11

### Removed

- Drop support for Python 3.6. (Pull #55)

### Added

- Add official support for Python 3.11. (Pull #55)
- Add official support for Python 3.9 and 3.10. (Pull #46 - Thanks @euri10)

### Fixed

- Ensure compatibility with mypy 0.990+, which made `no_implicit_optional` the default. (Pull #53 - Thanks @AllSeeingEyeTolledEweSew)

## 1.0.1 - 2020-06-08

### Fixed

- Update development status to `5 - Production/Stable`. (Pull #32)

## 1.0.0 - 2020-02-02

### Removed

- Drop `Lifespan` and `LifespanMiddleware`. Please use Starlette's built-in lifespan capabilities instead. (Pull #27)

### Fixed

- Use `sniffio` for auto-detecting the async environment. (Pull #28)
- Enforce 100% test coverage on CI. (Pull #29)

### Changed

- Enforce importing from the top-level package by switching to private internal modules. (Pull #26)

## 0.6.0 - 2019-11-29

### Changed

- Move `Lifespan` to the `lifespan` module. (Pull #21)
- Refactor `LifespanManager` to drop dependency on `asynccontextmanager` on 3.6. (Pull #20)

## 0.5.0 - 2019-11-29

- Enter Beta development status.

### Removed

- Remove `curio` support. (Pull #18)

### Added

- Ship binary distributions (wheels) alongside source distributions.

### Changed

- Use custom concurrency backends instead of `anyio` for asyncio and trio support. (Pull #18)

## 0.4.2 - 2019-10-06

### Fixed

- Ensure `py.typed` is bundled with the package so that type checkers can detect type annotations. (Pull #16)

## 0.4.1 - 2019-09-29

### Fixed

- Improve error handling in `LifespanManager` (Pull #11):
  - Exceptions raised in the context manager body or during shutdown are now properly propagated.
  - Unsupported lifespan is now also detected when the app calls `send()` before calling having called `receive()` at least once.

## 0.4.0 - 2019-09-29

- Enter Alpha development status.

## 0.3.1 - 2019-09-29

### Added

- Add configurable timeouts to `LifespanManager`. (Pull #10)

## 0.3.0 - 2019-09-29

### Added

- Add `LifespanManager` for sending lifespan events into an ASGI app. (Pull #5)

## 0.2.0 - 2019-09-28

### Added

- Add `LifespanMiddleware`, an ASGI middleware to add lifespan support to an ASGI app. (Pull #9)

## 0.1.0 - 2019-09-28

### Added

- Add `Lifespan`, an ASGI app implementing the lifespan protocol with event handler registration support. (Pull #7)

## 0.0.2 - 2019-09-28

### Fixed

- Installation from PyPI used to fail due to missing `MANIFEST.in`.

## 0.0.1 - 2019-09-28

### Added

- Empty package.
