# DeepSeek 字幕翻译改进

## 概述

对 YouDoub 项目的字幕翻译功能进行了重大改进，专门优化了 DeepSeek API 的使用体验。

## 新功能特性

### 1. 一次性提交整个字幕文件翻译 (`--whole-file`)

**优势：**
- AI 可以理解整个字幕的上下文，确保翻译更连贯
- 避免了分批翻译可能导致的上下文断层
- 特别适合叙事性内容和需要保持语境的对话

**使用方法：**
```bash
uv run youdoub yt translate-subs --lang zh-CN --backend deepseek --whole-file
```

### 2. 优化的翻译提示词

新的提示词专门为字幕翻译设计：
- 要求自然流畅的语序，不要逐句直译
- 适当调整句子结构以符合目标语言表达习惯
- 保持原文语气和风格
- 专业术语和专有名词保持英文原样

### 3. 智能时间轴合并 (`--merge-timelines`)

**功能：**
- 自动合并持续时间过短的字幕片段
- 减少字幕闪烁，提高观看体验
- 可配置最短持续时间阈值

**使用方法：**
```bash
uv run youdoub yt translate-subs --lang zh-CN --merge-timelines --min-duration 1500
```

## 命令行选项

### 新增选项

- `--whole-file`: 一次性提交整个字幕文件进行翻译
- `--merge-timelines`: 启用时间轴合并功能
- `--min-duration <毫秒>`: 设置最短字幕持续时间，默认 1000ms

### 完整命令示例

```bash
# 基础翻译（保持原有功能）
uv run youdoub yt translate-subs --lang zh-CN --backend deepseek

# 高质量翻译：一次性提交整个文件
uv run youdoub yt translate-subs --lang zh-CN --backend deepseek --whole-file

# 高质量翻译 + 时间轴优化
uv run youdoub yt translate-subs --lang zh-CN --backend deepseek --whole-file --merge-timelines

# 自定义时间轴合并阈值
uv run youdoub yt translate-subs --lang zh-CN --backend deepseek --whole-file --merge-timelines --min-duration 2000
```

## 技术实现

### 核心改进

1. **上下文感知翻译**: 通过一次性提交获得全局上下文理解
2. **智能文本分割**: 改进的翻译结果解析算法，支持序号标记
3. **时间轴优化**: 基于持续时间的智能合并算法
4. **错误处理**: 增强的重试机制和容错处理

### API 使用优化

- 充分利用 DeepSeek chat 模型的上下文理解能力
- 优化的提示词设计，确保翻译质量
- 合理的批次大小设置，避免 API 限制

## 使用建议

### 何时使用 `--whole-file`
- 字幕文件不大（建议 < 50KB 文本）
- 内容具有叙事性或需要保持上下文连贯性
- 对翻译质量要求较高

### 何时使用 `--merge-timelines`
- 原始字幕片段过短，观看时闪烁明显
- 需要优化用户观看体验
- 适用于演讲、教程等内容

### 性能考虑
- `--whole-file` 模式会增加 API 调用时间，但提高翻译质量
- 大文件建议仍使用分批模式以确保稳定性
- 时间轴合并会减少总字幕条目数

## 示例输出

### 原始字幕
```
1
00:00:00,000 --> 00:00:02,000
Hello world!

2
00:00:02,000 --> 00:00:04,000
This is a test.
```

### 优化后翻译（使用 `--whole-file --merge-timelines`）
```
1
00:00:00,000 --> 00:00:04,000
你好世界！这是一个测试。
```

## 故障排除

### 常见问题

1. **翻译结果行数不匹配**
   - 系统会自动尝试多种分割策略
   - 如仍有问题，会使用回退分割方法

2. **API 调用超时**
   - 增加 `--batch-size` 参数减少单次处理量
   - 或改用分批模式（去掉 `--whole-file`）

3. **时间轴合并过度**
   - 增加 `--min-duration` 值
   - 或完全关闭 `--merge-timelines`

## 兼容性

- 向后兼容所有现有功能
- 支持所有原有命令行选项
- 可以与现有工作流无缝集成