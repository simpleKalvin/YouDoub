from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Optional
import re
from ..utils.llm_adapters import get_translator


DEFAULT_PROMPT = "将以下文本翻译为 【目标语言】。文中涉及发音示例、专有名词或英文原词的部分请保持英文原样，不要翻译,只翻译其他能翻译的部分，文本：【文本】"


def parse_srt(path: Path) -> List[Dict]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    parts = [p.strip() for p in text.split("\n\n") if p.strip()]
    out = []
    for part in parts:
        lines = part.splitlines()
        if len(lines) < 2:
            continue
        idx = lines[0].strip()
        times = lines[1].strip()
        body = "\n".join(l.rstrip() for l in lines[2:]).strip()
        if "-->" not in times:
            continue
        start, end = [t.strip() for t in times.split("-->")]
        out.append({"index": idx, "start": start, "end": end, "text": body})
    return out


def write_srt(path: Path, entries: List[Dict]) -> None:
    parts = []
    for e in entries:
        parts.append(str(e["index"]))
        parts.append(f"{e['start']} --> {e['end']}")
        parts.append(e["text"])
        parts.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(parts), encoding="utf-8")


def batch_entries(entries: List[Dict], max_chars: int = 1000, max_items: int = 10) -> List[List[Dict]]:
    batches: List[List[Dict]] = []
    cur: List[Dict] = []
    cur_chars = 0
    for e in entries:
        length = len(e.get("text", "")) + 1
        if cur and (cur_chars + length > max_chars or len(cur) >= max_items):
            batches.append(cur)
            cur = []
            cur_chars = 0
        cur.append(e)
        cur_chars += length
    if cur:
        batches.append(cur)
    return batches


def split_translated_text(translated: str, n: int, originals: List[Dict]) -> List[str]:
    # Try simple newline split first
    lines = [ln.strip() for ln in translated.splitlines() if ln.strip()]
    if len(lines) == n:
        return lines

    # Fallback: split by sentence punctuation while preserving approximate lengths
    # naive sentence split
    sents = re.split(r'(?<=[。.!?！？])\s*', translated.strip())
    sents = [s for s in sents if s.strip()]
    if len(sents) >= n:
        # group sentences into n buckets by length
        buckets = [[] for _ in range(n)]
        lens = [len(o.get("text","")) for o in originals]
        total = sum(lens) or 1
        # desired proportion per bucket
        proportions = [l/total for l in lens]
        # assign sentences greedily to match proportions
        idx = 0
        for sent in sents:
            buckets[idx].append(sent)
            # move idx forward sometimes
            idx = (idx + 1) % n
        return [" ".join(b) for b in buckets]

    # As last resort, split translated string into n almost-equal chunks by characters
    translated = translated.strip()
    L = len(translated)
    if L == 0:
        return ["" for _ in range(n)]
    chunk_size = max(1, L // n)
    out = [translated[i*chunk_size:(i+1)*chunk_size].strip() for i in range(n)]
    # append remainder to last
    if n*chunk_size < L:
        out[-1] += translated[n*chunk_size:].strip()
    return out


def translate_srt_file(
    input_path: Path,
    output_path: Path,
    target_lang: str,
    backend: str = "deepseek",
    api_key: Optional[str] = None,
    prompt_template: str = DEFAULT_PROMPT,
    batch_size_chars: int = 30000,  # DeepSeek API limit: ~30K chars for stable processing
    max_items_per_batch: int = 200,  # Limit to 200 entries per batch for API stability
    verify_ssl: bool = True,
):
    import time
    start_time = time.time()

    print(f"📄 解析 SRT 文件: {input_path}")
    entries = parse_srt(input_path)
    if not entries:
        raise RuntimeError("No SRT entries parsed")

    print(f"📊 总字幕条目: {len(entries)}")
    print(f"🤖 初始化翻译器: {backend}")

    translator = get_translator(name=backend, api_key=api_key, verify_ssl=verify_ssl)

    print(f"📦 创建批次 (最大 {batch_size_chars} 字符, {max_items_per_batch} 条目/批)")
    batches = batch_entries(entries, max_chars=batch_size_chars, max_items=max_items_per_batch)
    print(f"🔢 总批次数: {len(batches)}")

    translated_texts: List[str] = []
    total_processed = 0

    for i, batch in enumerate(batches, 1):
        batch_start_time = time.time()

        # 显示当前批次信息
        batch_chars = sum(len(e["text"]) for e in batch)
        print(f"\n🔄 批次 {i}/{len(batches)} - {len(batch)} 条目 ({batch_chars} 字符)")

        # build batch text
        texts = [e["text"] for e in batch]
        batch_text = "\n".join(texts)

        # call translator
        print(f"📡 调用 {backend} API...")
        translated = translator.translate(batch_text, target_lang, prompt_template)

        # map translated back to items
        parts = split_translated_text(translated, len(batch), batch)
        if len(parts) != len(batch):
            print(f"⚠️  翻译结果数量不匹配，重试分割...")
            parts = split_translated_text(translated, len(batch), batch)

        for p in parts:
            translated_texts.append(p.strip())

        total_processed += len(batch)
        batch_time = time.time() - batch_start_time

        print(f"✅ 批次 {i} 完成 - 处理了 {len(batch)} 条目 (用时: {batch_time:.1f}s)")
        print(f"📈 总进度: {total_processed}/{len(entries)} 条目 ({total_processed/len(entries)*100:.1f}%)")

    if len(translated_texts) != len(entries):
        # safety: if mismatch, pad with empty strings
        # but better to raise so user notices
        raise RuntimeError(f"翻译条目数与原条目数不匹配: {len(translated_texts)} vs {len(entries)}")

    print(f"\n📝 构建翻译后的字幕文件...")
    # build new entries
    new_entries = []
    for e, tr in zip(entries, translated_texts):
        new_entries.append({"index": e["index"], "start": e["start"], "end": e["end"], "text": tr})

    print(f"💾 写入文件: {output_path}")
    write_srt(output_path, new_entries)

    total_time = time.time() - start_time
    print(f"\n🎉 翻译完成！总用时: {total_time:.1f}s")
    print(f"📊 平均速度: {len(entries)/total_time:.1f} 条目/秒")
    print(f"💡 API 调用次数: {len(batches)}")
