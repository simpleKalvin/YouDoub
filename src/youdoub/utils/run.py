from __future__ import annotations

import shlex
import subprocess
from pathlib import Path
from typing import Iterable, Sequence


class CommandError(RuntimeError):
    pass


def run_cmd(
    args: Sequence[str],
    *,
    cwd: Path | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess:
    """Run a command, streaming stdout/stderr to the terminal."""
    # Avoid shell=True for safety.
    try:
        return subprocess.run(
            list(args),
            cwd=str(cwd) if cwd else None,
            check=check,
        )
    except subprocess.CalledProcessError as e:
        cmd = " ".join(shlex.quote(a) for a in args)
        raise CommandError(f"Command failed ({e.returncode}): {cmd}") from e

