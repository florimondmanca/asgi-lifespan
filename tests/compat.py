try:
    ExceptionGroup = ExceptionGroup
except NameError:  # pragma: no cover
    from exceptiongroup import ExceptionGroup  # type: ignore
