#!/usr/bin/env python3
"""Quick test for whole-file SRT translation flow (may call the configured translator)."""

from pathlib import Path
from src.youdoub.subtitles.translate import translate_srt_file

def run_test():
    # Files are now in work/VIDEO_ID/subs/
    work = Path("work") / "VIDEO_ID" / "subs"
    src = work / "asr.en.srt"
    out = work / "asr.test.zh.srt"
    if not src.exists():
        print("Sample SRT not found:", src)
        return

    print("Running whole-file translation test (will call configured translator)...")
    try:
        translate_srt_file(
            input_path=src,
            output_path=out,
            target_lang="zh-CN",
            backend="deepseek",
            whole_file=True,
        )
        print("Output written to", out)
    except Exception as e:
        print("Translation test failed:", e)

if __name__ == "__main__":
    run_test()
