#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from pathlib import Path

from setuptools import find_packages, setup


def get_version(package: str) -> str:
    version = Path("src", package, "__version__.py").read_text()
    match = re.search("__version__ = ['\"]([^'\"]+)['\"]", version)
    assert match is not None
    return match.group(1)


def get_long_description() -> str:
    with open("README.md", encoding="utf8") as readme:
        with open("CHANGELOG.md", encoding="utf8") as changelog:
            return readme.read() + "\n\n" + changelog.read()


setup(
    name="asgi-lifespan",
    python_requires=">=3.6",
    version=get_version("asgi_lifespan"),
    url="https://github.com/florimondmanca/asgi-lifespan",
    license="MIT",
    description="Programmatic startup/shutdown of ASGI apps.",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    author="Florimond Manca",
    author_email="florimond.manca@gmail.com",
    packages=find_packages("src"),
    package_dir={"": "src"},
    install_requires=["sniffio", "async_exit_stack; python_version < '3.7'"],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
