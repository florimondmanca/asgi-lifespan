import nox

nox.options.stop_on_first_error = True

source_files = ("asgi_lifespan", "tests", "setup.py", "noxfile.py")


@nox.session(reuse_venv=True)
def lint(session: nox.sessions.Session) -> None:
    session.install("autoflake", "black", "flake8", "isort", "seed-isort-config")

    session.run("autoflake", "--in-place", "--recursive", *source_files)
    session.run("seed-isort-config", "--application-directories=asgi_lifespan")
    session.run(
        "isort", "--project=asgi_lifespan", "--recursive", "--apply", *source_files
    )
    session.run("black", "--target-version=py36", *source_files)

    check(session)


@nox.session(reuse_venv=True)
def check(session: nox.sessions.Session) -> None:
    session.install(
        "black", "flake8", "flake8-bugbear", "flake8-comprehensions", "isort", "mypy"
    )

    session.run("black", "--check", "--diff", "--target-version=py36", *source_files)
    session.run("flake8", *source_files)
    session.run("mypy", "asgi_lifespan")
    session.run(
        "isort",
        "--check",
        "--diff",
        "--project=asgi_lifespan",
        "--recursive",
        *source_files,
    )


@nox.session(python=["3.6", "3.7", "3.8"])
def test(session: nox.sessions.Session) -> None:
    session.install("-r", "requirements.txt")
    args = (
        session.posargs
        if session.python == "3.6"
        else ("--cov-fail-under=100", *session.posargs)
    )
    session.run("python", "-m", "pytest", *args)
