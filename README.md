# YouDoub

YouTube 视频下载、字幕翻译并上传到 BiliBili 的 CLI 工具

## 功能特性

- 📥 从 YouTube 下载视频
- 🎤 语音识别生成字幕 (支持 GPU/CPU)
- 🌐 多语言字幕翻译
- 📤 自动上传到 BiliBili

## 快速开始

### 在 Ubuntu 上安装和设置

1. **克隆项目**
   ```bash
   git clone <your-repo-url>
   cd YouDoub
   ```

2. **使用 Makefile 快速设置环境**
   ```bash
   # 检查系统要求
   make check-system

   # 完整设置 (推荐)
   make setup

   # 或者分步执行:
   # make install-uv    # 安装 uv 包管理器
   # make init          # 初始化虚拟环境
   # make install       # 安装项目依赖
   ```

3. **验证安装**
   ```bash
   make run
   ```

### 手动安装 (备选方案)

如果不想使用 Makefile，也可以手动安装：

```bash
# 安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc

# 初始化环境
uv venv
source .venv/bin/activate

# 安装依赖
uv pip install -e .
```

## 使用方法

### 下载视频
```bash
uv run youdoub yt dl "https://www.youtube.com/watch?v=VIDEO_ID"
```

### 生成字幕 (ASR)
```bash
uv run youdoub yt asr
```

### 翻译字幕
```bash
uv run youdoub yt translate-subs --lang zh-CN --backend deepseek
```

## Makefile 命令

| 命令 | 描述 |
|------|------|
| `make help` | 显示所有可用命令 |
| `make check-system` | 检查系统是否满足要求 |
| `make install-uv` | 安装 uv 包管理器 |
| `make init` | 初始化虚拟环境 |
| `make install` | 安装项目依赖 |
| `make dev-install` | 安装开发依赖 |
| `make run` | 运行 YouDoub CLI |
| `make test` | 运行测试 |
| `make clean` | 清理缓存文件 |
| `make setup` | 完整环境设置 |

## 系统要求

- Python >= 3.11
- Ubuntu/Debian 系统
- curl (用于安装 uv)

## 依赖

主要依赖包：
- typer: CLI 框架
- rich: 美化终端输出
- pydantic: 数据验证
- httpx: HTTP 客户端
- yt-dlp: YouTube 下载器
- faster-whisper: 语音识别
- openai: AI 接口

## 许可证

[请添加许可证信息]