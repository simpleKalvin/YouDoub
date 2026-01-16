"""
配置管理系统

使用 pydantic BaseSettings 管理项目配置，支持环境变量、.env 文件和命令行参数。
兼容 pydantic 2.x (需要 pydantic-settings 包) 和旧版本。
"""

import os
from pathlib import Path
from typing import Optional

# 兼容性导入：pydantic 2.x 将 BaseSettings 移到了 pydantic-settings
try:
    from pydantic_settings import BaseSettings
except ImportError:
    # 回退到旧版本 pydantic 的 BaseSettings
    from pydantic import BaseSettings

from pydantic import Field, validator


class YouDoubConfig(BaseSettings):
    """
    YouDoub 项目主配置类
    
    配置项优先级：
    1. 命令行参数
    2. 环境变量
    3. .env 文件
    4. 默认值
    
    环境变量命名约定：YOUDOUB_<SECTION>_<NAME>
    """
    
    # 工作目录配置
    workdir: Path = Field(
        default=Path("./work"),
        description="默认工作目录，视频、字幕和配置文件存储位置"
    )
    
    model_dir: Path = Field(
        default=Path("./models"),
        description="语音识别模型下载和缓存目录"
    )
    
    # 翻译配置
    deepseek_api_key: Optional[str] = Field(
        default=None,
        description="DeepSeek API 密钥，必需翻译功能"
    )
    
    deepseek_api_url: str = Field(
        default="https://api.deepseek.com",
        description="DeepSeek API 端点 URL"
    )
    
    default_translation_model: str = Field(
        default="deepseek-chat",
        description="默认翻译模型，支持 deepseek-chat 或 deepseek-reasoner"
    )
    
    translation_batch_size_chars: int = Field(
        default=30000,
        ge=1000,
        le=100000,
        description="翻译批处理最大字符数，DeepSeek API 推荐 30000"
    )
    
    translation_batch_max_items: int = Field(
        default=200,
        ge=1,
        le=500,
        description="翻译批处理最大条目数，推荐 200"
    )
    
    translation_timeout: int = Field(
        default=120,
        ge=30,
        le=300,
        description="翻译 API 调用超时时间（秒）"
    )
    
    verify_ssl: bool = Field(
        default=True,
        description="是否验证 SSL 证书"
    )
    
    # 字幕处理配置
    min_subtitle_duration_ms: int = Field(
        default=1000,
        ge=500,
        le=5000,
        description="最短字幕持续时间（毫秒），用于时间轴合并"
    )
    
    merge_short_timelines: bool = Field(
        default=True,
        description="是否合并短时间轴条目"
    )
    
    # 日志配置
    log_level: str = Field(
        default="INFO",
        description="日志级别：DEBUG, INFO, WARNING, ERROR, CRITICAL"
    )
    
    enable_file_logging: bool = Field(
        default=True,
        description="是否启用文件日志"
    )
    
    # BiliBili 上传配置
    biliup_binary: Optional[str] = Field(
        default=None,
        description="biliup 可执行文件路径，如果不在 PATH 中则需要指定"
    )
    
    # 缓存配置
    enable_translation_cache: bool = Field(
        default=True,
        description="是否启用翻译缓存，可显著提升重复翻译速度"
    )
    
    # 内部状态
    _instance: Optional["YouDoubConfig"] = None
    
    class Config:
        env_prefix = "YOUDOUB_"
        env_file = ".env"
        env_file_encoding = "utf-8"
        
    @validator("workdir", "model_dir", pre=True)
    def validate_paths(cls, v):
        """将字符串路径转换为 Path 对象"""
        if isinstance(v, str):
            return Path(v).expanduser().resolve()
        return v
    
    @validator("deepseek_api_key", pre=True)
    def validate_api_key(cls, v):
        """从环境变量获取 API 密钥（如果未提供）"""
        if v is None:
            # 尝试从 DEEPSEEK_API_KEY 环境变量获取（兼容现有代码）
            v = os.environ.get("DEEPSEEK_API_KEY")
        return v
    
    @validator("deepseek_api_url", pre=True)
    def validate_api_url(cls, v):
        """从环境变量获取 API URL（如果未提供）"""
        if v == "https://api.deepseek.com":
            # 尝试从 DEEPSEEK_API_URL 环境变量获取（兼容现有代码）
            env_url = os.environ.get("DEEPSEEK_API_URL")
            if env_url:
                return env_url
        return v
    
    @property
    def translation_cache_path(self) -> Path:
        """翻译缓存文件路径"""
        return self.workdir / "cache" / "translation.jsonl"
    
    @property
    def log_dir(self) -> Path:
        """日志目录路径"""
        return self.workdir / "logs"
    
    def ensure_directories(self) -> None:
        """确保所有必要的目录存在"""
        self.workdir.mkdir(parents=True, exist_ok=True)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        (self.workdir / "cache").mkdir(parents=True, exist_ok=True)
        (self.workdir / "subs").mkdir(parents=True, exist_ok=True)
        (self.workdir / "out").mkdir(parents=True, exist_ok=True)
        (self.workdir / "bili").mkdir(parents=True, exist_ok=True)


# 全局配置实例
_config_instance: Optional[YouDoubConfig] = None


def get_config() -> YouDoubConfig:
    """
    获取全局配置实例（单例模式）
    
    第一次调用时加载配置，后续调用返回相同实例。
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = YouDoubConfig()
        _config_instance.ensure_directories()
    return _config_instance


def reload_config() -> YouDoubConfig:
    """
    重新加载配置
    
    用于环境变量或 .env 文件变更后更新配置。
    """
    global _config_instance
    _config_instance = YouDoubConfig()
    _config_instance.ensure_directories()
    return _config_instance


def override_config(**kwargs) -> YouDoubConfig:
    """
    临时覆盖配置项
    
    用于测试或命令行参数覆盖，返回新的配置实例但不影响全局实例。
    """
    config = YouDoubConfig(**kwargs)
    config.ensure_directories()
    return config