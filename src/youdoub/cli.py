"""
YouDoub - YouTube to BiliBili Pipeline with Subtitle Translation
"""
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

try:
    from . import __version__
except ImportError:
    # Allow running as standalone script
    __version__ = "0.1.0"

app = typer.Typer(
    name="youdoub",
    help="YouTube -> ASR (Buzz) -> BiliBili Upload Pipeline",
    no_args_is_help=True,
)
console = Console()

from .youtube import cli as youtube_cli

# Sub-commands will be registered here
app.add_typer(youtube_cli.app, name="yt")
from .bilibili import cli as bilibili_cli

app.add_typer(bilibili_cli.app, name="bili")


def version_callback(value: bool):
    if value:
        console.print(f"YouDoub v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="显示版本并退出。",
    )
):
    """YouDoub - YouTube 到 B站上传管道"""
    pass


# NOTE: Remaining commands are implemented as subcommand groups.
# Next: add `asr` group (Buzz ASR) and `bili` group (biliup config/upload).


if __name__ == "__main__":
    app()
