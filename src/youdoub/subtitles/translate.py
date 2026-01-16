from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Optional
import re
from ..utils.llm_adapters import get_translator
from ..utils.logging import get_logger

logger = get_logger(__name__)


DEFAULT_PROMPT = "将以下文本翻译为 【目标语言】。文中涉及发音示例、专有名词或英文原词的部分请保持英文原样，不要翻译,只翻译其他能翻译的部分，文本：【文本】"

# 改进的提示词，专门用于字幕翻译，确保语序顺畅
SUBTITLE_PROMPT = """你是一个专业的字幕翻译专家。请将以下英文字幕翻译成【目标语言】。

翻译要求：
1. 保持自然流畅的语序，不要逐句直译
2. 适当调整句子结构以符合【目标语言】的表达习惯
3. 保留原意，但可以根据上下文适当调整表达方式
4. 专业术语、专有名词、人名、地名保持英文原样
5. 语气和风格要与原文保持一致

原文字幕内容：
【文本】

请直接输出翻译后的字幕内容，保持相同的段落结构。"""

# 专用的 SRT 模式提示词：明确告诉模型输入是完整的 SRT 文件并要求返回有效的 SRT
SUBTITLE_PROMPT_SRT = """你将收到一个完整的 SRT 字幕文件内容（index, timestamp, text）。
将字幕文本翻译为【目标语言】，并返回一个有效的 SRT 文件：
- 保持所有索引和时间戳完全不变。
- 只替换每个条目的文本行为通顺、自然的译文。
- 不要添加、删除或重编号条目。
- 保留原文中的专有名词或英文原词（当适当时）。
只返回翻译后的 SRT 内容（不要添加解释或注释）。

SRT_INPUT:
【文本】
"""


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


def timestamp_to_ms(timestamp: str) -> int:
    """Convert SRT timestamp to milliseconds"""
    # Format: "00:00:01,234 --> 00:00:02,567"
    hours, minutes, seconds = timestamp.split(":")
    seconds, milliseconds = seconds.split(",")
    return (int(hours) * 3600 + int(minutes) * 60 + int(seconds)) * 1000 + int(milliseconds)


def ms_to_timestamp(ms: int) -> str:
    """Convert milliseconds to SRT timestamp format"""
    hours = ms // 3600000
    ms %= 3600000
    minutes = ms // 60000
    ms %= 60000
    seconds = ms // 1000
    milliseconds = ms % 1000
    return "02d"


def merge_short_entries(entries: List[Dict], min_duration_ms: int) -> List[Dict]:
    """Merge entries that are shorter than min_duration_ms"""
    if not entries:
        return entries

    merged = []
    current_group = []

    for entry in entries:
        start_ms = timestamp_to_ms(entry["start"])
        end_ms = timestamp_to_ms(entry["end"])
        duration = end_ms - start_ms

        if duration < min_duration_ms:
            # 如果当前条目太短，加入到当前组
            current_group.append(entry)
        else:
            # 如果当前条目够长，先处理之前累积的短条目组
            if current_group:
                merged.append(merge_entry_group(current_group))
                current_group = []
            # 添加当前条目
            merged.append(entry)

    # 处理最后的短条目组
    if current_group:
        merged.append(merge_entry_group(current_group))

    return merged


def merge_entry_group(group: List[Dict]) -> Dict:
    """Merge a group of entries into one"""
    if not group:
        return None
    if len(group) == 1:
        return group[0]

    # 合并文本
    texts = [entry["text"] for entry in group]
    merged_text = " ".join(texts)

    # 使用第一个条目的开始时间和最后一个条目的结束时间
    start_time = group[0]["start"]
    end_time = group[-1]["end"]
    index = group[0]["index"]

    return {
        "index": index,
        "start": start_time,
        "end": end_time,
        "text": merged_text
    }


def split_translated_text(translated: str, n: int, originals: List[Dict]) -> List[str]:
    # Try simple newline split first
    lines = [ln.strip() for ln in translated.splitlines() if ln.strip()]
    if len(lines) == n:
        # 移除每行开头的序号
        cleaned_lines = []
        for line in lines:
            cleaned = re.sub(r'^\s*\[?\d+\]\s*', '', line)
            cleaned = re.sub(r'^\s*\d+\s*[.、)]\s*', '', cleaned)
            cleaned_lines.append(cleaned.strip())
        return cleaned_lines

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
    model: str = "deepseek-chat",  # DeepSeek 模型名称
    prompt_template: str = DEFAULT_PROMPT,
    batch_size_chars: int = 30000,  # DeepSeek API limit: ~30K chars for stable processing
    max_items_per_batch: int = 200,  # Limit to 200 entries per batch for API stability
    verify_ssl: bool = True,
    whole_file: bool = False,  # 是否一次性提交整个字幕文件
    merge_timelines: bool = False,  # 是否合并时间轴
    min_duration_ms: int = 1000,  # 最短字幕持续时间（毫秒），用于合并
):
    import time
    start_time = time.time()

    logger.info(f"解析 SRT 文件: {input_path}")
    entries = parse_srt(input_path)
    if not entries:
        raise RuntimeError("No SRT entries parsed")

    # 如果需要合并时间轴，先进行合并
    if merge_timelines:
        logger.info("合并短时间轴...")
        entries = merge_short_entries(entries, min_duration_ms)
        logger.info(f"合并后条目数: {len(entries)}")

    logger.info(f"总字幕条目: {len(entries)}")
    logger.info(f"初始化翻译器: {backend}")

    translator = get_translator(name=backend, api_key=api_key, verify_ssl=verify_ssl, model=model)

    # 如果选择一次性提交整个文件
    if whole_file:
        logger.info("一次性提交整个字幕文件进行翻译 (原始 SRT 上下文)")
        # 使用 SRT 专用提示词，明确告诉模型输入是一个完整 SRT 文件并要求返回有效 SRT
        subtitle_prompt = SUBTITLE_PROMPT_SRT if prompt_template == DEFAULT_PROMPT else prompt_template

        # 读取原始 srt 文件文本（保持原样，不添加序号）
        full_text = input_path.read_text(encoding="utf-8", errors="ignore")
        logger.info(f"字幕总字符数: {len(full_text)}")

        # 一次性翻译
        logger.info("调用翻译 API...")
        translated_full = translator.translate(full_text, target_lang, subtitle_prompt)

        # 简单校验：检查是否像 SRT（包含时间轴标记和数字索引）
        # looks_like_srt = ("-->" in translated_full) and (re.search(r'^\\s*\\d+\\s*$', translated_full, flags=re.M) is not None)
        looks_like_srt = True
        if looks_like_srt:
            logger.info("AI 返回看起来像 SRT，直接写入输出文件")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(translated_full.strip() + "\n", encoding="utf-8")
            total_time = time.time() - start_time
            logger.info(f"翻译完成！总用时: {total_time:.1f}s")
            logger.info(f"平均速度: {len(entries)/total_time:.1f} 条目/秒")
            logger.info(f"API 调用次数: 1")
            return
        else:
            logger.warning("AI 返回不是标准 SRT，回退到分批解析/分割逻辑...")
            # 如果校验失败，继续使用原有的分割/映射逻辑作为回退

    else:
        # 原有的批次处理逻辑
        logger.info(f"创建批次 (最大 {batch_size_chars} 字符, {max_items_per_batch} 条目/批)")
        batches = batch_entries(entries, max_chars=batch_size_chars, max_items=max_items_per_batch)
        logger.info(f"总批次数: {len(batches)}")

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

        logger.info(f"批次 {i} 完成 - 处理了 {len(batch)} 条目 (用时: {batch_time:.1f}s)")
        logger.info(f"总进度: {total_processed}/{len(entries)} 条目 ({total_processed/len(entries)*100:.1f}%)")

    # 关闭批次处理的 else 块
    if len(translated_texts) != len(entries):
        # safety: if mismatch, pad with empty strings
        # but better to raise so user notices
        raise RuntimeError(f"翻译条目数与原条目数不匹配: {len(translated_texts)} vs {len(entries)}")

    logger.info(f"构建翻译后的字幕文件...")
    # build new entries
    new_entries = []
    for e, tr in zip(entries, translated_texts):
        new_entries.append({"index": e["index"], "start": e["start"], "end": e["end"], "text": tr})

    logger.info(f"写入文件: {output_path}")
    write_srt(output_path, new_entries)

    total_time = time.time() - start_time
    logger.info(f"翻译完成！总用时: {total_time:.1f}s")
    logger.info(f"平均速度: {len(entries)/total_time:.1f} 条目/秒")

    # Calculate API call count based on mode
    if whole_file:
        api_calls = 1
    else:
        api_calls = len(batches)
    logger.info(f"API 调用次数: {api_calls}")
