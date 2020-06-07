# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## 1.0.1 (June 8, 2020)

### Fixed

- Update development status to `5 - Production/Stable`. (Pull #32)

## 1.0.0 (February 2, 2020)

### Removed

- Drop `Lifespan` and `LifespanMiddleware`. Please use Starlette's built-in lifespan capabilities instead. (Pull #27)

### Fixed

- Use `sniffio` for auto-detecting the async environment. (Pull #28)

- Enforce 100% test coverage on CI. (Pull #29)

### Changed

- Enforce importing from the top-level package by switching to private internal modules. (Pull #26)

## 0.6.0 (November 29, 2019)

### Changed

- Move `Lifespan` to the `lifespan` module. (Pull #21)
- Refactor `LifespanManager` to drop dependency on `asynccontextmanager` on 3.6. (Pull #20)

## 0.5.0 (November 29, 2019)

- Enter Beta development status.

### Removed

- Remove `curio` support. (Pull #18)

### Added

- Ship binary distributions (wheels) alongside source distributions.

### Changed

- Use custom concurrency backends instead of `anyio` for asyncio and trio support. (Pull #18)

## 0.4.2 (October 6, 2019)

### Fixed

- Ensure `py.typed` is bundled with the package so that type checkers can detect type annotations. (Pull #16)

## 0.4.1 (September 29, 2019)

### Fixed

- Improve error handling in `LifespanManager` (Pull #11):
  - Exceptions raised in the context manager body or during shutdown are now properly propagated.
  - Unsupported lifespan is now also detected when the app calls `send()` before calling having called `receive()` at least once.

## 0.4.0 (September 29, 2019)

- Enter Alpha development status.

## 0.3.1 (September 29, 2019)

### Added

- Add configurable timeouts to `LifespanManager`. (Pull #10)

## 0.3.0 (September 29, 2019)

### Added

- Add `LifespanManager` for sending lifespan events into an ASGI app. (Pull #5)

## 0.2.0 (September 28, 2019)

### Added

- Add `LifespanMiddleware`, an ASGI middleware to add lifespan support to an ASGI app. (Pull #9)

## 0.1.0 (September 28, 2019)

### Added

- Add `Lifespan`, an ASGI app implementing the lifespan protocol with event handler registration support. (Pull #7)

## 0.0.2 (September 28, 2019)

### Fixed

- Installation from PyPI used to fail due to missing `MANIFEST.in`.

## 0.0.1 (September 28, 2019)

### Added

- Empty package.
