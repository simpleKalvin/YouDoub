# YouDoub TODO

> Goal: A minimal, step-by-step CLI pipeline to搬运 YouTube 学习视频：下载视频 → 获取/生成字幕 → 用 Ollama 翻译字幕 → 生成输出字幕 → 使用 biliup 上传到 B 站。
> 
> Principles: 功能优先、职责分明、可断点续跑、每一步可单独命令行执行、输出目录结构固定。


## 0. 项目基线与约定
- [ ] 统一采用包模式（src/youdoub）作为实现位置，`pyproject.toml` 提供 `youdoub` CLI entry。
- [ ] 约定一个 workdir（例如 `./work/<slug>`）作为每个视频的工作空间。
- [ ] 约定目录结构：
  - `workdir/meta.json`（YouTube 元信息）
  - `workdir/video.<ext>`（视频文件）
  - `workdir/subs/source.<lang>.vtt|srt`（原字幕）
  - `workdir/subs/source.<lang>.srt`（统一后的中间字幕）
  - `workdir/cache/translation.jsonl`（翻译缓存/断点）
  - `workdir/subs/translated.zh-Hans.srt`（翻译后字幕）
  - `workdir/out/zh-Hans.srt`、`workdir/out/bilingual.srt`（最终输出）
  - `workdir/bili/upload_result.json`（上传结果）


## 1. CLI 命令结构（Typer）
- [x] 顶层：`youdoub --help` / `--version`
- [x] 子命令组：
  - [x] `youdoub yt ...`（YouTube 相关）
  - [x] `youdoub sub ...`（字幕处理/翻译）
  - [x] `youdoub bili ...`（上传相关）


## 2. YouTube：下载视频（yt-dlp）
- [ ] 命令：`youdoub yt dl --url <url> --workdir <dir>`
- [ ] 行为：
  - [ ] 调用 `yt-dlp` 下载最佳画质/音频合并
  - [ ] 输出 `meta.json`（至少包含 title/uploader/upload_date/description/webpage_url 等）
  - [ ] 输出视频到 `workdir/video.*`（或固定命名 `video.mp4`）
  - [ ] 支持重复执行：如果文件存在则跳过/可用 `--force` 重下


## 3. YouTube：获取字幕（yt-dlp）
- [ ] 命令：`youdoub yt sub --workdir <dir> --lang en`（lang 默认 en）
- [ ] 行为：
  - [ ] 优先 `--write-subs` 下载人工字幕
  - [ ] 可选策略：找不到时 fallback `--write-auto-subs`（待确认）
  - [ ] 将 vtt 转换为统一 SRT：`workdir/subs/source.<lang>.srt`
  - [ ] 若无字幕：明确报错并退出（或提示使用 `yt asr`）


## 4. ASR（占位命令）
- [ ] 命令：`youdoub yt asr --workdir <dir> --lang en`
- [ ] 行为：
  - [ ] 仅输出清晰提示“未实现：后续接入 Whisper/faster-whisper”
  - [ ] 预留输出路径：`workdir/subs/asr.<lang>.srt`


## 5. 字幕解析与规范化
- [ ] 支持读写 SRT（内部数据结构：index/start_ms/end_ms/text）
- [ ] 基础 normalize：
  - [ ] 去多余空行/空白
  - [ ] 合并非常短的连续片段（可选）
  - [ ] 保留时间轴不变（优先）


## 6. Ollama 翻译（核心）
- [x] 命令：`youdoub sub translate --workdir <dir> --model xieweicong95/HY-MT1.5-1.8B --lang en`
- [x] 依赖：Ollama HTTP API（默认 `http://localhost:11434`）
- [x] 行为：
  - [x] 读取 `source.<lang>.srt`，按批次翻译
  - [x] 批量翻译：`--batch-size N`（默认 10）
  - [x] 使用严格 JSON 协议输出，解析失败自动重试（`--max-retries`）
  - [x] 翻译缓存（断点续跑）：`workdir/cache/translation.jsonl`
    - [x] key = sha256(model + src_lang + tgt_lang + normalized_text)
  - [x] 输出 `workdir/subs/translated.zh-Hans.srt`


## 7. 生成最终字幕
- [x] 命令：`youdoub sub render --workdir <dir> --mode zh|bilingual`
- [x] 行为：
  - [x] `mode=zh` 输出纯中文 `workdir/out/zh-Hans.srt`
  - [x] `mode=bilingual` 输出双语（译文+原文）`workdir/out/bilingual.srt`


## 8. 上传到 B 站（biliup 包装）
- [x] 命令：
  - [x] 生成配置：`youdoub bili config --workdir <dir> ...`
  - [x] 上传：`youdoub bili upload --workdir <dir>`
- [x] 行为：
  - [x] 生成 `workdir/bili/biliup.yaml`（可能需要你按自己 biliup 版本手动微调字段）
  - [x] Python 内部使用 `subprocess` 调用 `biliup upload -c <yaml>`
  - [x] 将上传返回码写入 `workdir/bili/upload_result.json`


## 9. README（最小使用说明）
- [ ] 写入最小示例流程：
  - [ ] `uv sync`
  - [ ] `uv run youdoub yt dl ...`
  - [ ] `uv run youdoub yt sub ...`
  - [ ] `uv run youdoub sub translate ...`
  - [ ] `uv run youdoub sub render ...`
  - [ ] `uv run youdoub bili upload ...`


## 10. 待你确认的选项（影响实现细节）
- [x] 字幕策略：fallback auto
- [x] biliup 使用方式：config file

