# YouDoub

YouTube 视频下载、字幕翻译并上传到 BiliBili 的 CLI 工具

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Package management: uv](https://img.shields.io/badge/package%20manager-uv-orange.svg)](https://github.com/astral-sh/uv)

## ✨ 功能特性

- **📥 视频下载** - 从 YouTube 下载视频，支持多种格式和质量选项
- **🎤 语音识别生成字幕** - 使用 faster-whisper 进行 ASR（支持 GPU/CPU 加速）
- **🌐 多语言字幕翻译** - 支持 DeepSeek API，多种模型选择（deepseek-chat、deepseek-reasoner）
- **🔄 智能字幕处理** - 时间轴合并、格式优化、智能文本分割
- **📤 一键上传到 BiliBili** - 自动配置生成，完整工作流支持
- **🔧 完整流程自动化** - 从下载、翻译到上传的一站式解决方案
- **📊 统一日志系统** - 结构化日志记录，支持文件和控制台输出

## 🚀 快速开始

### 使用 Makefile（推荐）

```bash
# 克隆项目
git clone <your-repo-url>
cd YouDoub

# 完整环境设置（推荐）
make setup

# 或者分步执行：
make install-uv    # 安装 uv 包管理器
make init          # 初始化虚拟环境
make install       # 安装项目依赖
```

### 手动安装

```bash
# 安装 uv 包管理器
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc

# 初始化环境
uv venv
source .venv/bin/activate

# 安装依赖
uv pip install -e .

# 配置环境变量（可选）
cp env.example .env
# 编辑 .env 文件添加你的 API keys
```

### 安装 biliup（BiliBili 上传功能）

```bash
# 使用 uv 安装（推荐）
uv pip install biliup

# 验证安装
biliup --version

# 配置 BiliBili 账号
biliup login
```

## 📖 详细文档

- [📤 BiliBili 投稿功能指南](docs/bilibili_upload.md) - 一键投稿命令和工作流程
- [🔧 biliup 安装和配置](docs/biliup_setup.md) - biliup 安装、配置和故障排除
- [🌐 DeepSeek 字幕翻译改进](docs/translation_improvements.md) - 高质量翻译功能详解
- [📁 项目架构与开发指南](CODEBUDDY.md) - 详细的项目架构和开发说明

## 🎯 核心使用示例

### 完整工作流程（从 YouTube 到 BiliBili）

```bash
# 1. 下载视频（自动获取元数据和字幕，VIDEO_ID 从 URL 自动提取）
uv run youdoub yt dl "https://www.youtube.com/watch?v=VIDEO_ID"
# 也支持从浏览器复制的带转义字符的URL：uv run youdoub yt dl https://www.youtube.com/watch\?v\=VIDEO_ID

# 2. 生成双语字幕（如果原始字幕不存在）
uv run youdoub yt asr --video-id VIDEO_ID --lang en

# 3. 高质量翻译字幕到中文
uv run youdoub yt translate-subs \
  --video-id VIDEO_ID \
  --lang zh-CN \
  --backend deepseek \
  --whole-file \
  --merge-timelines \
  --model deepseek-reasoner

# 4. 一键投稿到 BiliBili
uv run youdoub bili submit \
  --video-id VIDEO_ID \
  --title "视频标题" \
  --desc "详细的视频描述" \
  --tags "科技,教程,翻译" \
  --tid 123
```

### 分步操作

```bash
# 仅下载视频（VIDEO_ID 从 URL 自动提取）
uv run youdoub yt dl "URL"

# 仅下载 YouTube 字幕
uv run youdoub yt sub --video-id VIDEO_ID

# 基础字幕翻译
uv run youdoub yt translate-subs --video-id VIDEO_ID --lang zh-CN

# 生成 BiliBili 上传配置
uv run youdoub bili config --video-id VIDEO_ID --title "标题" --desc "描述"

# 执行上传
uv run youdoub bili upload --video-id VIDEO_ID

# 查看完整工作流程指南
uv run youdoub bili workflow
```

## 🛠️ 项目结构

```
YouDoub/
├── src/youdoub/                    # 主代码库
│   ├── cli.py                     # CLI 入口点
│   ├── paths.py                   # 工作空间路径管理
│   ├── youtube/                   # YouTube 相关功能
│   │   ├── cli.py                 # YouTube 子命令
│   │   ├── downloader.py          # 视频下载器
│   │   └── subtitles.py           # 字幕工具
│   ├── bilibili/                  # BiliBili 相关功能
│   │   └── cli.py                 # BiliBili 子命令
│   ├── subtitles/                 # 字幕处理核心
│   │   └── translate.py           # 翻译引擎
│   └── utils/                     # 工具模块
│       ├── logging.py             # 统一日志配置
│       ├── llm_adapters.py        # AI 翻译适配器
│       ├── hash.py                # 哈希工具
│       └── run.py                 # 进程执行工具
├── tests/                         # 测试套件
│   ├── unit/                      # 单元测试
│   │   ├── youtube/
│   │   ├── bilibili/
│   │   └── subtitles/
│   └── integration/               # 集成测试
├── docs/                          # 文档
│   ├── bilibili_upload.md
│   ├── biliup_setup.md
│   └── translation_improvements.md
├── work/                          # 工作目录（自动生成）
├── pyproject.toml                 # 项目配置
├── Makefile                       # 构建脚本
├── uv.lock                        # 依赖锁定
└── README.md                      # 本文件
```

## 🔧 Makefile 命令参考

| 命令 | 描述 |
|------|------|
| `make help` | 显示所有可用命令 |
| `make setup` | 完整环境设置（推荐） |
| `make install-uv` | 安装 uv 包管理器 |
| `make init` | 初始化虚拟环境 |
| `make install` | 安装项目依赖 |
| `make dev-install` | 安装开发依赖（测试、格式化） |
| `make test` | 运行所有测试 |
| `make test-bili` | 运行 BiliBili 相关测试 |
| `make clean` | 清理缓存和临时文件 |
| `make run` | 运行 YouDoub CLI |

## ⚙️ 配置说明

### 环境变量

```bash
# DeepSeek API 配置（必需）
export DEEPSEEK_API_KEY="your-api-key-here"
export DEEPSEEK_API_URL="https://api.deepseek.com"  # 可选，自定义端点

# 工作目录配置（可选）
export YOUDOUB_WORKDIR="./work"  # 默认工作目录
export MODEL_DIR="./models"      # 语音识别模型目录
```

### 配置管理系统

YouDoub 提供了一个统一的配置管理系统 (`src/youdoub/config.py`)，基于 pydantic-settings 构建，支持多级配置优先级：

1. **命令行参数** - 最高优先级
2. **环境变量** - 次高优先级，前缀 `YOUDOUB_`
3. **.env 文件** - 项目根目录下的 `.env` 文件
4. **默认值** - 合理的默认配置

**核心配置类**：
```python
from youdoub.config import get_config

config = get_config()
print(f"工作目录: {config.workdir}")
print(f"模型目录: {config.model_dir}")
print(f"翻译批次大小: {config.translation_batch_size_chars}")
```

**主要配置项**：
- `workdir`: 工作目录路径（默认 `./work`）
- `model_dir`: 语音识别模型目录（默认 `./models`）
- `deepseek_api_key`: DeepSeek API 密钥（必需）
- `translation_batch_size_chars`: 翻译批处理字符数（默认 30000）
- `min_subtitle_duration_ms`: 最短字幕持续时间（默认 1000ms）
- `log_level`: 日志级别（默认 INFO）

**使用方法**：
```python
# 在模块中获取配置
from youdoub.config import get_config

config = get_config()
logger.info(f"使用工作目录: {config.workdir}")
```

### 命令行选项

常用选项：
- `--workdir/-w`：指定工作目录路径
- `--verbose/-v`：详细日志输出
- `--debug`：调试模式，输出更多信息

## 📝 开发指南

### 代码格式化

```bash
# 安装开发依赖
make dev-install

# 格式化代码
uv run black src/
uv run isort src/

# 代码检查
uv run ruff check src/
uv run mypy src/
```

### 运行测试

```bash
# 运行所有测试
make test

# 运行特定模块测试
uv run python -m pytest tests/unit/youtube/ -v

# 运行集成测试
uv run python -m pytest tests/integration/ -v
```

### 添加新功能

1. 在相应模块目录下创建新文件或扩展现有文件
2. 在 `src/youdoub/cli.py` 中注册新的子命令
3. 编写单元测试和集成测试
4. 更新文档

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 [MIT 许可证](LICENSE)。

## 🙏 致谢

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube 视频下载
- [faster-whisper](https://github.com/guillaumekln/faster-whisper) - 快速语音识别
- [DeepSeek](https://www.deepseek.com/) - AI 翻译服务
- [biliup](https://github.com/ForgQi/biliup) - BiliBili 上传工具

---

**YouDoub** - 让跨平台视频翻译和分享变得更简单！ 🎬➡️📝➡️🚀