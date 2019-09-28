#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import typing
from pathlib import Path

from setuptools import setup


def get_version(package: str) -> str:
    version = Path(package, "__version__.py").read_text()
    match = re.search("__version__ = ['\"]([^'\"]+)['\"]", version)
    assert match is not None
    return match.group(1)


def get_long_description() -> str:
    with open("README.md", encoding="utf8") as readme:
        with open("CHANGELOG.md", encoding="utf8") as changelog:
            return readme.read() + "\n\n" + changelog.read()


def get_packages(package: str) -> typing.List[str]:
    return [str(path.parent) for path in Path(package).glob("**/__init__.py")]


setup(
    name="asgi-lifespan",
    python_requires=">=3.6",
    version=get_version("asgi_lifespan"),
    url="https://github.com/florimondmanca/asgi-lifespan",
    license="MIT",
    description="Lifespan protocol support for ASGI apps and libraries.",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    author="Florimond Manca",
    author_email="florimond.manca@gmail.com",
    packages=get_packages("asgi_lifespan"),
    install_requires=[
        "anyio",
        "async_generator; python_version < '3.7'",
        "async_exit_stack; python_version < '3.7'",
    ],
    include_package_data=True,
    package_data={"asgi_lifespan": ["py.typed"]},
    zip_safe=False,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
)
