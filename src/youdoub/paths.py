from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class WorkPaths:
    """Filesystem layout for a single video workspace (workdir)."""

    root: Path

    @property
    def meta_json(self) -> Path:
        return self.root / "meta.json"

    @property
    def video(self) -> Path:
        # we will download as video.mp4 (merged) for simplicity
        return self.root / "video.mp4"

    @property
    def subs_dir(self) -> Path:
        return self.root / "subs"

    def source_sub_any(self, lang: str) -> list[Path]:
        # possible locations we might create
        return [
            self.subs_dir / f"source.{lang}.vtt",
            self.subs_dir / f"source.{lang}.srt",
        ]

    def source_sub_srt(self, lang: str) -> Path:
        return self.subs_dir / f"source.{lang}.srt"

    def translated_sub_srt(self, target: str = "zh-Hans") -> Path:
        return self.subs_dir / f"translated.{target}.srt"

    @property
    def cache_dir(self) -> Path:
        return self.root / "cache"

    @property
    def translation_cache(self) -> Path:
        return self.cache_dir / "translation.jsonl"

    @property
    def out_dir(self) -> Path:
        return self.root / "out"

    def out_zh(self, target: str = "zh-Hans") -> Path:
        return self.out_dir / f"{target}.srt"

    @property
    def out_bilingual(self) -> Path:
        return self.out_dir / "bilingual.srt"

    @property
    def bili_dir(self) -> Path:
        return self.root / "bili"

    @property
    def bili_config(self) -> Path:
        return self.bili_dir / "biliup.yaml"

    @property
    def bili_result(self) -> Path:
        return self.bili_dir / "upload_result.json"


def ensure_workdir(root: Path) -> WorkPaths:
    root = root.expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    wp = WorkPaths(root=root)
    wp.subs_dir.mkdir(parents=True, exist_ok=True)
    wp.cache_dir.mkdir(parents=True, exist_ok=True)
    wp.out_dir.mkdir(parents=True, exist_ok=True)
    wp.bili_dir.mkdir(parents=True, exist_ok=True)
    return wp

