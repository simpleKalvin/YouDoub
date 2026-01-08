from __future__ import annotations

import shutil
from pathlib import Path

from ..utils.run import run_cmd


def _pick_downloaded_sub(workdir: Path, lang: str) -> Path | None:
    """Pick a downloaded subtitle file from yt-dlp output.

    We download into workdir/subs with a fixed template; yt-dlp still appends
    extensions (.vtt/.srt) depending on availability.
    """
    subs_dir = workdir / "subs"
    candidates = sorted(
        [
            *subs_dir.glob(f"source.{lang}*.vtt"),
            *subs_dir.glob(f"source.{lang}*.srt"),
        ]
    )
    return candidates[0] if candidates else None


def download_youtube_subtitles(
    *,
    url: str,
    workdir: Path,
    lang: str = "en",
    fallback_auto: bool = True,
    force: bool = False,
) -> Path:
    """Download subtitles via yt-dlp.

    Tries human subtitles first, then optionally falls back to auto subtitles.
    Returns path to the downloaded subtitle file.
    """
    subs_dir = workdir / "subs"
    subs_dir.mkdir(parents=True, exist_ok=True)

    # If we already have normalized srt and not force, return it.
    normalized_srt = subs_dir / f"source.{lang}.srt"
    if normalized_srt.exists() and not force:
        return normalized_srt

    # 1) human subtitles
    base_args = [
        "yt-dlp",
        "--skip-download",
        "--no-part",
        "--sub-lang",
        lang,
        "--sub-format",
        "vtt/srt",
        "-o",
        str(subs_dir / f"source.{lang}.%(ext)s"),
        url,
    ]

    run_cmd([*base_args, "--write-subs"], check=False)
    picked = _pick_downloaded_sub(workdir, lang)

    # 2) fallback to auto
    if picked is None and fallback_auto:
        run_cmd([*base_args, "--write-auto-subs"], check=False)
        picked = _pick_downloaded_sub(workdir, lang)

    if picked is None:
        raise FileNotFoundError(f"No subtitles found for lang={lang}.")

    # Normalize to source.<lang>.srt
    if picked.suffix.lower() == ".srt":
        if picked != normalized_srt:
            shutil.copyfile(picked, normalized_srt)
    else:
        # Convert vtt -> srt using yt-dlp's convert-subs if possible
        # We'll call yt-dlp --convert-subs srt to regenerate as srt.
        # NOTE: yt-dlp outputs alongside the original in the same dir.
        run_cmd(
            [
                "yt-dlp",
                "--skip-download",
                "--no-part",
                "--sub-lang",
                lang,
                "--sub-format",
                "vtt",
                "--convert-subs",
                "srt",
                "--write-subs",
                "-o",
                str(subs_dir / f"source.{lang}.%(ext)s"),
                url,
            ],
            check=False,
        )

        # After conversion, try to find srt
        srt_candidates = sorted(subs_dir.glob(f"source.{lang}*.srt"))
        if not srt_candidates:
            raise FileNotFoundError("Subtitle conversion to srt failed.")
        shutil.copyfile(srt_candidates[0], normalized_srt)

    return normalized_srt

