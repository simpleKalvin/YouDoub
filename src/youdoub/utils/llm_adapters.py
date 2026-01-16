import os
import time
from typing import Optional

from openai import OpenAI


class Translator:
    """Abstract translator interface."""

    def translate(self, text: str, target_lang: str, prompt_template: str) -> str:
        raise NotImplementedError()


class DeepseekTranslator(Translator):
    def __init__(self, api_key: Optional[str] = None, api_url: Optional[str] = None, timeout: int = 120, verify_ssl: bool = True, model: str = "deepseek-chat"):
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        self.api_url = api_url or os.environ.get("DEEPSEEK_API_URL", "https://api.deepseek.com")
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.model = model
        if not self.api_key:
            raise RuntimeError("DEEPSEEK_API_KEY not provided (env DEEPSEEK_API_KEY or pass api_key)")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.api_url
        )

    def _build_prompt(self, text: str, target_lang: str, prompt_template: str) -> str:
        # Replace tokens if present. Support both bracketed and plain placeholders.
        p = prompt_template
        p = p.replace("【目标语言】", target_lang).replace("【文本】", text)
        p = p.replace("{target_lang}", target_lang).replace("{text}", text)
        return p

    def translate(self, text: str, target_lang: str, prompt_template: str) -> str:
        prompt = self._build_prompt(text, target_lang, prompt_template)

        # simple retry
        backoff = 1.0
        for attempt in range(4):
            try:
                if attempt > 0:
                    print(f"🔄 重试 API 调用 (尝试 {attempt + 1}/4)...")

                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant"},
                        {"role": "user", "content": prompt},
                    ],
                    stream=False,
                    timeout=self.timeout,
                    temperature=1.3
                )

                content = response.choices[0].message.content
                if content:
                    print(f"📨 API 响应: {len(content)} 字符")
                else:
                    print("⚠️  API 返回空响应")

                return content
            except Exception as e:
                print(f"❌ API 调用失败: {str(e)}")
                if attempt == 3:
                    print("💥 所有重试都失败了")
                    raise
                print(f"⏳ 等待 {backoff:.1f} 秒后重试...")
                time.sleep(backoff)
                backoff *= 2.0


def get_translator(name: str = "deepseek", api_key: Optional[str] = None, api_url: Optional[str] = None, verify_ssl: bool = True, model: str = "deepseek-chat") -> Translator:
    name_l = (name or "deepseek").lower()
    if name_l == "deepseek":
        return DeepseekTranslator(api_key=api_key, api_url=api_url, verify_ssl=verify_ssl, model=model)
    # Placeholder for other backends; raise if not implemented
    raise RuntimeError(f"Translator backend not implemented: {name}")

