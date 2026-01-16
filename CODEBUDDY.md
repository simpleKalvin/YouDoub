# CODEBUDDY.md

This file provides guidance to CodeBuddy Code when working with code in this repository.

## Project Overview

YouDoub is a CLI tool for downloading YouTube videos, translating subtitles, and uploading to BiliBili. It implements a complete pipeline: YouTube → ASR (speech-to-text) → Translation → BiliBili Upload.

## Common Commands

### Development Setup

```bash
# Complete environment setup (recommended for new setups)
make setup

# Or step-by-step:
make install-uv    # Install uv package manager
make init          # Initialize virtual environment
make install       # Install project dependencies
make install-biliup # Install biliup for BiliBili upload

# Install dev dependencies (testing, linting)
make dev-install

# Verify installation
make run
```

### Running Tests

```bash
# Run all tests
make test

# Test specific BiliBili functionality
make test-bili

# Run specific test file
uv run python test_bili_submit.py
```

### Building and Linting

```bash
# The project uses uv for dependency management and execution
# No separate build step needed - use `uv run youdoub` directly

# Format code (if dev deps installed)
uv run black src/
uv run isort src/

# Type check (if dev deps installed)
uv run mypy src/

# Lint (if dev deps installed)
uv run ruff check src/
```

### Main CLI Commands

All CLI commands are run via `uv run youdoub [command]`:

```bash
# Show help
uv run youdoub --help

# YouTube commands
uv run youdoub yt dl "https://youtube.com/watch?v=VIDEO_ID"  # Download video (VIDEO_ID auto-extracted)
# Also supports: uv run youdoub yt dl https://youtube.com/watch\?v\=VIDEO_ID (handles escaped URLs)
uv run youdoub yt asr --video-id VIDEO_ID                     # Generate subtitles via ASR
uv run youdoub yt translate-subs --video-id VIDEO_ID --lang zh-CN --backend deepseek --whole-file  # Translate subtitles
uv run youdoub yt sub --video-id VIDEO_ID                     # Download YouTube subtitles

# BiliBili commands
uv run youdoub bili submit --video-id VIDEO_ID --title "Title" --desc "Description" --tags "tag1,tag2" --tid 123  # One-click upload
uv run youdoub bili config --video-id VIDEO_ID --title "Title" --desc "Description"  # Generate biliup config
uv run youdoub bili upload --video-id VIDEO_ID                # Upload using existing config
uv run youdoub bili workflow                                  # Show complete workflow

# Base work directory can be customized with YOUDOUB_WORKDIR env var or --workdir/-w flag
export YOUDOUB_WORKDIR=./my-videos
uv run youdoub yt dl "URL"  # Uses ./my-videos/VIDEO_ID/
```

### Cleanup

```bash
# Clean cache and temporary files
make clean
```

## Architecture

### Project Structure

```
src/youdoub/
├── cli.py                 # Main CLI entry point with typer
├── paths.py               # WorkPaths dataclass for workspace layout
├── youtube/
│   ├── cli.py            # YouTube sub-commands (dl, asr, translate-subs)
│   ├── downloader.py     # YouTube video download using yt-dlp
│   └── subtitles.py      # Subtitle utilities
├── bilibili/
│   └── cli.py            # BiliBili sub-commands (config, upload, submit)
├── subtitles/
│   └── translate.py      # Core translation logic with SRT parsing
└── utils/
    ├── llm_adapters.py   # DeepSeek/OpenAI adapter for translation
    ├── hash.py           # Hashing utilities
    └── run.py            # Process execution utilities
```

### Key Design Patterns

**Workspace Layout (WorkPaths)**: The project uses a standardized workspace directory structure managed by `paths.py:WorkPaths`. Each video gets its own subdirectory under the base work directory (default: `./work/` or `YOUDOUB_WORKDIR` env var). All video files, subtitles, metadata, and BiliBili configs are organized within each video's workspace:

- `BASE_WORKDIR/VIDEO_ID/video.mp4` - Downloaded video
- `BASE_WORKDIR/VIDEO_ID/meta.json` - Video metadata from YouTube
- `BASE_WORKDIR/VIDEO_ID/subs/` - Subtitle files (source, ASR, translated)
- `BASE_WORKDIR/VIDEO_ID/out/` - Final output subtitles
- `BASE_WORKDIR/VIDEO_ID/bili/` - BiliBili upload configs and results
- `BASE_WORKDIR/VIDEO_ID/cache/` - Translation cache

**CLI Command Structure**: Uses typer for CLI with nested sub-commands:
- `youdoub yt <command>` - YouTube operations (download, ASR, translate)
- `youdoub bili <command>` - BiliBili operations (config, upload, submit)

**Translation Pipeline**:
1. Parse SRT into list of `{"index", "start", "end", "text"}` entries
2. Batch entries by character count (default: 30000 chars/batch for DeepSeek)
3. Call LLM adapter (DeepSeek) with batched text
4. Split translated response back into individual entries
5. Reconstruct SRT with translated text preserving timestamps
6. Optionally merge short timeline entries for better UX

**Translation Modes**:
- **Batch mode** (default): Process subtitles in batches of up to 200 entries or 30K chars
- **Whole-file mode** (`--whole-file`): Submit entire SRT file to AI for better context coherence

**BiliBili Integration**:
- Uses external `biliup` CLI tool for uploads (not a Python library)
- Generates `biliup.yaml` config file in `work/bili/`
- One-click `submit` command combines config generation + upload with validation

### Important Implementation Details

**ASR (Speech Recognition)**:
- Uses `faster-whisper` with configurable models (tiny/base/small/medium/large)
- Model files are cached in `./models/` directory (configurable via `--model-dir`)
- Automatically prefers audio stream files (`*.webm`, `*.m4a`) over video for ASR
- Outputs SRT format to `work/subs/asr.<lang>.srt`

**Translation Backend**:
- Primary backend: DeepSeek API (via OpenAI-compatible API)
- API key required via `DEEPSEEK_API_KEY` environment variable or `--api-key` flag
- Supports two DeepSeek models: `deepseek-chat` (default) and `deepseek-reasoner`
- Implements retry logic with exponential backoff (4 attempts)
- Temperature set to 1.3 for more varied translations

**Subtitle Processing**:
- Custom SRT parser that handles various formatting edge cases
- Timeline merging: combines entries shorter than `min_duration_ms` (default: 1000ms)
- Smart text splitting: handles numbered lists, sentence boundaries, and character-based fallback

**YouTube Download**:
- Uses `yt-dlp` Python API (not CLI)
- Downloads best video+audio and merges to MP4
- Optionally downloads YouTube captions (manual and auto-generated)
- Can keep separate audio/video streams for ASR optimization
- Fallback to metadata-only if video download fails

## Environment Variables

- `YOUDOUB_WORKDIR` - Base work directory for all videos (default: `./work`)
- `DEEPSEEK_API_KEY` - Required for DeepSeek translation backend
- `DEEPSEEK_API_URL` - Optional custom DeepSeek API endpoint (default: https://api.deepseek.com)

Create a `.env` file using the template in `env.example`:

```bash
cp env.example .env
# Then edit .env with your actual API keys
```

## Migration Notes

**Backwards Compatibility**: The new version organizes videos under `BASE_WORKDIR/VIDEO_ID/` subdirectories instead of directly in `BASE_WORKDIR/`. Existing workflows that downloaded files directly into `./work/` will need to either:

1. Move existing video files to `./work/VIDEO_ID/` subdirectories, or
2. Re-run `youdoub yt dl` commands with the new structure

All downstream commands (`asr`, `translate-subs`, `bili` subcommands) now require `--video-id` to specify which video workspace to operate on.

## External Dependencies

- **biliup**: Must be installed separately for BiliBili upload functionality
  - Install: `uv pip install biliup` or `make install-biliup`
  - Configure: `biliup login` (once)
  - Version compatibility: Check BILIUP_SETUP.md for troubleshooting

## Workflow Examples

**Complete workflow (YouTube → BiliBili)**:
```bash
# 1. Download video with metadata (VIDEO_ID auto-extracted from URL)
uv run youdoub yt dl "https://youtube.com/watch?v=VIDEO_ID"

# 2. Generate subtitles via ASR (if needed)
uv run youdoub yt asr --video-id VIDEO_ID --lang en

# 3. Translate subtitles to Chinese
uv run youdoub yt translate-subs --video-id VIDEO_ID --lang zh-CN --backend deepseek --whole-file --merge-timelines

# 4. One-click upload to BiliBili
uv run youdoub bili submit --video-id VIDEO_ID --title "Video Title" --desc "Description" --tags "tech,tutorial" --tid 123
```

**Translate only (no ASR needed) - using YouTube captions**:
```bash
uv run youdoub yt dl "URL"  # Downloads auto/manual captions (VIDEO_ID auto-extracted)
uv run youdoub yt translate-subs --video-id VIDEO_ID --source work/VIDEO_ID/subs/source.en.srt --lang zh-CN
```

**Multiple videos in parallel**:
```bash
# Each video gets its own subdirectory under BASE_WORKDIR (default: ./work)
# VIDEO_ID is auto-extracted from URL, no need for separate --workdir
uv run youdoub yt dl "URL1"  # Creates ./work/VIDEO_ID1/
uv run youdoub yt dl "URL2"  # Creates ./work/VIDEO_ID2/

# Then process each video separately:
uv run youdoub yt translate-subs --video-id VIDEO_ID1 --lang zh-CN
uv run youdoub bili submit --video-id VIDEO_ID1 --title "Title 1"

uv run youdoub yt translate-subs --video-id VIDEO_ID2 --lang zh-CN
uv run youdoub bili submit --video-id VIDEO_ID2 --title "Title 2"
```

## Key Files Reference

- `src/youdoub/cli.py:24-26` - CLI command registration
- `src/youdoub/paths.py:8-69` - WorkPaths dataclass defining workspace structure
- `src/youdoub/youtube/cli.py:287-349` - translate-subs command implementation
- `src/youdoub/subtitles/translate.py:204-332` - translate_srt_file core logic
- `src/youdoub/utils/llm_adapters.py:15-73` - DeepseekTranslator with retry logic
- `src/youdoub/bilibili/cli.py:137-236` - One-click submit command

## Testing

Test files are in the root directory:
- `test_bili_submit.py` - BiliBili upload functionality tests
- `test_translate_*.py` - Translation feature tests
- `test_deepseek.py` - DeepSeek API connectivity tests

Run with: `uv run python <test_file>.py`
