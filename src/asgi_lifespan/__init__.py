from .__version__ import __description__, __title__, __version__
from ._exceptions import LifespanNotSupported
from ._manager import LifespanManager

__all__ = [
    "__description__",
    "__title__",
    "__version__",
    "LifespanManager",
    "LifespanNotSupported",
]
