"""Prevent downgrading Poetry when editing a lock file."""

from operator import imod
from pathlib import Path
import re
from cleo.io.io import IO
from poetry.plugins.plugin import Plugin
from poetry.__version__ import __version__ as poetry_version
from poetry.core.constraints.version import Version

import git
from poetry.poetry import Poetry
import typer

VERSION_RE = re.compile(r"Poetry (\d+\.\d+\.\d+)")
POETRY_LOCK_FILE_NAME = "poetry.lock"


def parse_version(lock_header: str) -> Version:
    """Parse the Poetry version from the lock file header."""
    if not lock_header.startswith("# This file is automatically"):
        raise ValueError(f"Invalid lock file header: {lock_header}")

    if not (match := VERSION_RE.search(lock_header)):
        raise ValueError(f"Cannot parse version from {lock_header}")

    return Version(match.group(1))


def _find_current_version(lock_path: Path) -> Version:
    with lock_path.open() as f:
        current_header = f.readline()
    return parse_version(current_header)


def _find_previous_version(lock_path: Path, head: str = "HEAD") -> Version:
    try:
        previous_lock_content = git.Repo(
            lock_path, search_parent_directories=True
        ).git.cat_file("blob", f"{head}:{POETRY_LOCK_FILE_NAME}")
    except Exception as e:
        typer.echo(f"Cannot find previous lock file {type(e)} {e}")
        raise typer.Exit(1) from e

    try:
        previous_lock_header = previous_lock_content.split("\n")[0]
    except Exception as e:
        typer.echo(f"Cannot parse previous lock file: {type(e)} {e}")
        raise typer.Exit(1) from e

    return parse_version(previous_lock_header)


def main(
    lock_path: Path = typer.Argument(
        default=Path.cwd() / POETRY_LOCK_FILE_NAME,
        help=f"Path to the lock file. Defaults to {POETRY_LOCK_FILE_NAME} in the current directory.",
        dir_okay=False,
        file_okay=True,
        exists=True,
    ),
    prev_ref: str = typer.Option(
        "HEAD", help="Git reference to the previous version of the lock file."
    ),
    require_same_version: bool = typer.Option(
        False,
        "--strict",
        help="Whether to require that the exact same version of Poetry is used. "
        "Otherwise, will promote upgrading Poetry to the latest version.",
    ),
) -> None:
    """Prevent downgrading Poetry when editing a lock file."""
    current_version = _find_current_version(lock_path)
    previous_version = _find_previous_version(lock_path, prev_ref)

    if require_same_version:
        if previous_version != current_version:
            typer.echo(
                "Poetry.lock version mismatch detected.\n"
                f"You are using Poetry {current_version} to edit poetry.lock previously generated with Poetry {previous_version}.\n"
                f"Run `poetry self update {previous_version}` to match your Poetry version."
            )
            raise typer.Exit(1)

    else:
        if previous_version > current_version:
            typer.echo(
                "Poetry.lock downgrade detected.\n"
                f"You are using Poetry {current_version} to edit poetry.lock previously generated with Poetry {previous_version}.\n"
                "Run `poetry self update` to update your Poetry version."
            )
            raise typer.Exit(1)

class PreventDowngradePlugin(Plugin):
    def activate(self, poetry: Poetry, io: IO) -> None:
        io.write_line("Checking for version downgrades...")
        current_version = Version(poetry_version)
        previous_version = _find_previous_version(poetry.locker.lock, self.option('prev_ref', 'HEAD'))

        if self.option('require_same_version', False):
            if previous_version != current_version:
                self.error(
                    "Poetry.lock version mismatch detected.\n"
                    f"You are using Poetry {current_version} to edit poetry.lock previously generated with Poetry {previous_version}.\n"
                    f"Run `poetry self update {previous_version}` to match your Poetry version."
                )
                raise typer.Exit(1)

        else:
            if previous_version > current_version:
                typer.echo(
                    "Poetry.lock downgrade detected.\n"
                    f"You are using Poetry {current_version} to edit poetry.lock previously generated with Poetry {previous_version}.\n"
                    "Run `poetry self update` to update your Poetry version."
                )
                raise typer.Exit(1)



if __name__ == "__main__":
    typer.run(main)
