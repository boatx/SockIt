import tempfile
from typing import Any

import nox
from nox.sessions import Session

PYTHON_VERSIONS = ("3.8", "3.7")
LOCATIONS = ("noxfile.py", "tests", "sockit")

nox.options.sessions = ("lint", "mypy", "pytype", "tests")


def install_with_constraints(
    session: Session, *args: str, **kwargs: Any
) -> None:
    with tempfile.NamedTemporaryFile() as requirements:
        session.run(
            "poetry",
            "export",
            "--dev",
            "--format=requirements.txt",
            f"--output={requirements.name}",
            external=True,
        )
        session.install(f"--constraint={requirements.name}", *args, **kwargs)


@nox.session(python=PYTHON_VERSIONS)
def tests(session: Session) -> None:
    args = session.posargs or ["--cov"]
    session.run("poetry", "install", "--no-dev", external=True)
    install_with_constraints(session, "coverage[toml]", "pytest", "pytest-cov")
    session.run("pytest", *args)


@nox.session(python=PYTHON_VERSIONS)
def lint(session: Session) -> None:
    args = session.posargs or LOCATIONS
    install_with_constraints(
        session,
        "flake8",
        "flake8-annotations",
        "flake8-bandit",
        "flake8-black",
        "flake8-bugbear",
        "flake8-isort",
    )
    session.run("flake8", *args)


@nox.session(python=PYTHON_VERSIONS)
def mypy(session: Session) -> None:
    args = session.posargs or LOCATIONS
    install_with_constraints(session, "mypy")
    session.run("mypy", *args)


@nox.session(python="3.7")
def pytype(session: Session) -> None:
    """Run the static type checker."""
    args = session.posargs or ["--disable=import-error", *LOCATIONS]
    install_with_constraints(session, "pytype")
    session.run("pytype", *args)
