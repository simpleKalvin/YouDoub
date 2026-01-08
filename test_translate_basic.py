#!/usr/bin/env python3
"""Basic test for translate functionality"""

import sys
import os
sys.path.insert(0, 'src')

def test_translate_imports():
    """Test that all translate modules can be imported"""
    try:
        from youdoub.translate.subtitle_translator import SubtitleTranslator, TranslatorConfig
        from youdoub.translate.cache import TranslationCache
        from youdoub.translate.clients.openai_client import OpenAIClient
        from youdoub.translate.clients.deepseek_client import DeepseekClient
        from youdoub.translate.ollama_client import OllamaClient
        print("✓ All translate modules imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

def test_basic_config():
    """Test basic configuration"""
    try:
        config = TranslatorConfig(model="test-model", batch_size=5)
        print(f"✓ Config created: model={config.model}, batch_size={config.batch_size}")
        return True
    except Exception as e:
        print(f"✗ Config creation failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing translate module...")
    success = True
    success &= test_translate_imports()
    success &= test_basic_config()

    if success:
        print("\n✅ All basic tests passed!")
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)