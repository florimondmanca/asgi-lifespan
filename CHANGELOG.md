# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## Unreleased

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
