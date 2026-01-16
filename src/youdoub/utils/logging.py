"""
统一日志配置模块

提供统一的日志配置，支持文件输出、控制台彩色输出和日志轮转。
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler


def setup_logging(
    workdir: Optional[Path] = None,
    level: str = "INFO",
    log_to_file: bool = True,
    log_to_console: bool = True,
) -> logging.Logger:
    """
    配置统一的日志系统
    
    Args:
        workdir: 工作目录，日志文件将保存在 workdir/logs/ 下
                如果为 None，则使用当前目录的 logs/ 文件夹
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: 是否输出到文件
        log_to_console: 是否输出到控制台
        
    Returns:
        配置好的 logger 实例
    """
    # 获取根 logger
    logger = logging.getLogger("youdoub")
    logger.setLevel(getattr(logging, level.upper()))
    
    # 清除现有的 handlers（避免重复）
    logger.handlers.clear()
    
    # 日志格式
    file_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台输出使用 Rich 的彩色格式
    console_formatter = logging.Formatter(
        fmt='%(message)s',
        datefmt='[%X]'
    )
    
    # 文件输出
    if log_to_file:
        if workdir is None:
            log_dir = Path("logs")
        else:
            log_dir = workdir / "logs"
        
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # 按日期轮转的日志文件
        file_handler = logging.handlers.TimedRotatingFileHandler(
            filename=log_dir / "youdoub.log",
            when="midnight",
            interval=1,
            backupCount=7,
            encoding="utf-8"
        )
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    # 控制台输出
    if log_to_console:
        console = Console()
        console_handler = RichHandler(
            console=console,
            show_time=True,
            show_level=True,
            show_path=True,
            rich_tracebacks=True,
            markup=True
        )
        console_handler.setLevel(getattr(logging, level.upper()))
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str = "youdoub") -> logging.Logger:
    """
    获取指定名称的 logger
    
    Args:
        name: logger 名称，默认为 "youdoub"
        
    Returns:
        logging.Logger 实例
    """
    return logging.getLogger(name)


# 默认 logger 实例
logger = get_logger()


if __name__ == "__main__":
    # 测试日志配置
    test_logger = setup_logging(level="DEBUG")
    test_logger.debug("调试信息")
    test_logger.info("普通信息")
    test_logger.warning("警告信息")
    test_logger.error("错误信息")
    test_logger.critical("严重错误")
    
    print("✅ 日志配置测试完成")