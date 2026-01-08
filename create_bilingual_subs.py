#!/usr/bin/env python3
"""Create bilingual subtitles from English and Chinese SRT files"""

import re
from pathlib import Path
from typing import List, Dict


def parse_srt(content: str) -> List[Dict]:
    """Parse SRT file content into entries"""
    parts = [p.strip() for p in content.split("\n\n") if p.strip()]
    entries = []

    for part in parts:
        lines = part.splitlines()
        if len(lines) < 3:
            continue

        # Extract index
        try:
            index = int(lines[0].strip())
        except ValueError:
            continue

        # Extract timestamp
        if "-->" not in lines[1]:
            continue
        timestamp = lines[1].strip()

        # Extract text (all remaining lines)
        text = "\n".join(lines[2:]).strip()

        entries.append({
            "index": index,
            "timestamp": timestamp,
            "text": text
        })

    return entries


def merge_subtitles(en_entries: List[Dict], zh_entries: List[Dict]) -> List[Dict]:
    """Merge English and Chinese subtitles into bilingual format"""
    bilingual_entries = []

    # Use the longer list as base
    max_len = max(len(en_entries), len(zh_entries))
    min_len = min(len(en_entries), len(zh_entries))

    for i in range(max_len):
        en_text = ""
        zh_text = ""

        # Get English text if available
        if i < len(en_entries):
            en_text = en_entries[i]["text"]

        # Get Chinese text if available
        if i < len(zh_entries):
            zh_text = zh_entries[i]["text"]

        # Clean Chinese text - remove English parts if they exist at the beginning
        if zh_text and en_text:
            # If Chinese text starts with English text, remove the English part
            if zh_text.startswith(en_text[:50]):  # Check first 50 chars
                zh_text = zh_text[len(en_text):].strip()
                # Remove leading punctuation
                zh_text = re.sub(r'^[.,\s]+', '', zh_text)

        # Create bilingual text
        bilingual_text = ""
        if zh_text:
            bilingual_text += zh_text
        if en_text and zh_text:
            bilingual_text += "\n"
        if en_text:
            bilingual_text += en_text

        # Use English entry as base for timestamp/index, fallback to Chinese
        base_entry = en_entries[i] if i < len(en_entries) else zh_entries[i]

        bilingual_entries.append({
            "index": base_entry["index"],
            "timestamp": base_entry["timestamp"],
            "text": bilingual_text.strip()
        })

    return bilingual_entries


def write_srt(entries: List[Dict], output_path: Path):
    """Write entries to SRT file"""
    parts = []
    for entry in entries:
        parts.append(str(entry["index"]))
        parts.append(entry["timestamp"])
        parts.append(entry["text"])
        parts.append("")  # Empty line between entries

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(parts), encoding="utf-8")


def main():
    # Input files
    en_file = Path("work/subs/asr.en.srt")
    zh_file = Path("work/subs/asr.zh-CN.srt")
    output_file = Path("work/subs/asr.bilingual.srt")

    if not en_file.exists():
        print(f"❌ 英文字幕文件不存在: {en_file}")
        return

    if not zh_file.exists():
        print(f"❌ 中文字幕文件不存在: {zh_file}")
        return

    print(f"📄 读取英文字幕: {en_file}")
    en_content = en_file.read_text(encoding="utf-8")
    en_entries = parse_srt(en_content)
    print(f"📊 英文条目数: {len(en_entries)}")

    print(f"📄 读取中文字幕: {zh_file}")
    zh_content = zh_file.read_text(encoding="utf-8")
    zh_entries = parse_srt(zh_content)
    print(f"📊 中文条目数: {len(zh_entries)}")

    print("🔀 合并字幕...")
    bilingual_entries = merge_subtitles(en_entries, zh_entries)

    print(f"💾 保存双语字幕: {output_file}")
    write_srt(bilingual_entries, output_file)

    print(f"✅ 完成！生成了 {len(bilingual_entries)} 个双语字幕条目")
    print(f"📂 输出文件: {output_file}")


if __name__ == "__main__":
    main()