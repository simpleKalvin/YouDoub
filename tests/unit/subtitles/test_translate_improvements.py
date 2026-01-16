#!/usr/bin/env python3
"""Test the improved translation functionality"""

import os
from pathlib import Path
from src.youdoub.subtitles.translate import translate_srt_file, parse_srt, merge_short_entries

def test_merge_timelines():
    """Test timeline merging functionality"""
    print("Testing timeline merging...")

    # Create test entries
    entries = [
        {"index": 1, "start": "00:00:00,000", "end": "00:00:01,000", "text": "Hello"},
        {"index": 2, "start": "00:00:01,000", "end": "00:00:01,500", "text": "world"},
        {"index": 3, "start": "00:00:01,500", "end": "00:00:03,000", "text": "This is a longer sentence that should not be merged"},
        {"index": 4, "start": "00:00:03,000", "end": "00:00:03,200", "text": "Short"},
        {"index": 5, "start": "00:00:03,200", "end": "00:00:03,400", "text": "words"},
    ]

    print(f"Original entries: {len(entries)}")
    for entry in entries:
        print(f"  {entry['index']}: {entry['start']} -> {entry['end']}: {entry['text']}")

    # Test merging with 800ms threshold
    merged = merge_short_entries(entries, 800)
    print(f"\nMerged entries: {len(merged)}")
    for entry in merged:
        print(f"  {entry['index']}: {entry['start']} -> {entry['end']}: {entry['text']}")

def test_parse_srt():
    """Test SRT parsing"""
    print("\nTesting SRT parsing...")

    # Test with the actual file (now in work/VIDEO_ID/subs/asr.en.srt)
    test_file = Path("work") / "VIDEO_ID" / "subs" / "asr.en.srt"
    if test_file.exists():
        entries = parse_srt(test_file)
        print(f"Parsed {len(entries)} entries from {test_file}")
        print("First 3 entries:")
        for i, entry in enumerate(entries[:3]):
            print(f"  {entry['index']}: {entry['start']} -> {entry['end']}: {entry['text'][:50]}...")
    else:
        print(f"Test file {test_file} not found")

def test_translation_structure():
    """Test translation function structure (without actually calling API)"""
    print("\nTesting translation function structure...")

    # This would require API key, so we'll just test the function signature
    from src.youdoub.utils.llm_adapters import get_translator

    try:
        # Try to create translator (will fail without API key, but tests structure)
        translator = get_translator("deepseek", api_key="test_key")
        print("Translator created successfully (structure test passed)")
    except Exception as e:
        if "DEEPSEEK_API_KEY" in str(e):
            print("API key validation working correctly")
        else:
            print(f"Unexpected error: {e}")

if __name__ == "__main__":
    test_merge_timelines()
    test_parse_srt()
    test_translation_structure()
    print("\nAll tests completed!")