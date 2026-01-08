from __future__ import annotations

import os
from pathlib import Path

import typer
from rich.console import Console
from faster_whisper import WhisperModel

from ..paths import ensure_workdir
from .downloader import download_youtube_video
import json
from typing import List
from ..subtitles.translate import translate_srt_file

app = typer.Typer(no_args_is_help=True)
console = Console()

@app.command("dl")
def dl(
    url: str = typer.Argument(..., help="YouTube 视频 URL"),
    workdir: Path = typer.Option(Path("./work"), "--workdir", "-w", help="工作目录"),
    force: bool = typer.Option(False, "--force", help="强制重新下载，即使文件已存在"),
    download_subs: bool = typer.Option(True, "--subs/--no-subs", help="同时下载字幕"),
    sub_lang: str = typer.Option("en", "--sub-lang", help="字幕语言（默认：en）"),
    keep_streams: bool = typer.Option(False, "--keep-streams", help="保留单独的音频和视频流文件"),
):
    """下载视频、元数据以及可选的字幕到工作目录。"""
    wp = ensure_workdir(workdir)
    download_youtube_video(
        url=url,
        video_out=wp.video,
        meta_out=wp.meta_json,
        force=force,
        download_subs=download_subs,
        sub_lang=sub_lang,
        keep_separate_streams=keep_streams
    )
    console.print(f"[green]完成[/green] 视频: {wp.video}")
    console.print(f"[green]完成[/green] 元数据:  {wp.meta_json}")
    if download_subs:
        console.print(f"[green]完成[/green] 字幕:  {wp.subs_dir}")
    if keep_streams:
        console.print(f"[green]完成[/green] 保留了音频和视频流文件")


@app.command("asr")
def asr(
    workdir: Path = typer.Option(Path("./work"), "--workdir", "-w", help="工作目录"),
    lang: str = typer.Option("en", "--lang", help="ASR 语言"),
    input_file: str = typer.Option(None, "--input", "-i", help="输入音频/视频文件路径（默认为 work/video.mp4）"),
    model: str = typer.Option("medium", "--model", "-m", help="Whisper 模型: tiny/base/small/medium/large-v1/large-v2/large-v3/large/distil-*系列/turbo (默认: medium)"),
    model_dir: str = typer.Option(None, "--model-dir", help="模型下载目录（默认为 ./models）"),
    force: bool = typer.Option(False, "--force", help="强制重新生成，即使文件已存在"),
):
    """ASR 语音识别（使用 faster-whisper）。"""
    wp = ensure_workdir(workdir)

    # 确定输入文件
    if input_file is None:
        # 优先使用音频流文件（如果存在），其次使用视频文件
        audio_files = list(workdir.glob("*.webm")) + list(workdir.glob("*.m4a"))
        if audio_files:
            input_file = str(audio_files[0])  # 使用第一个音频文件
        elif wp.video.exists():
            input_file = str(wp.video)
        else:
            console.print("[red]错误[/red] 未找到输入文件（音频流文件或 video.mp4）")
            raise typer.Exit(1)

    # 检查输入文件是否存在
    input_path = Path(input_file)
    if not input_path.exists():
        console.print(f"[red]错误[/red] 输入文件不存在: {input_file}")
        raise typer.Exit(1)

    # 设置默认模型目录
    if model_dir is None:
        model_dir = str(Path("./models"))
        console.print(f"使用默认模型目录: {model_dir}")

    # 确保模型目录存在
    Path(model_dir).mkdir(parents=True, exist_ok=True)

    # 确定输出文件路径
    output_file = wp.subs_dir / f"asr.{lang}.srt"
    if output_file.exists() and not force:
        console.print(f"[green]完成[/green] ASR 字幕已存在: {output_file}")
        return

    console.print(f"开始 ASR 处理...")
    console.print(f"输入文件: {input_file}")
    console.print(f"输出文件: {output_file}")
    console.print(f"语言: {lang}")
    console.print(f"模型: {model}")
    if model_dir:
        console.print(f"模型目录: {model_dir}")

    # 设置模型缓存目录
    if model_dir:
        os.environ["HF_HOME"] = model_dir
        os.environ["HUGGINGFACE_HUB_CACHE"] = model_dir

    try:
        # 初始化 Whisper 模型
        # 尝试 float16，如果不支持则回退到 float32
        model_instance = WhisperModel(
            model,
            device="auto",
            download_root=model_dir,
            local_files_only=False
        )

        # 进行语音识别
        console.print("正在进行语音识别，请稍候...")
        segments, info = model_instance.transcribe(
            str(input_path),
            language=lang if lang != "auto" else None,
            beam_size=5,
            patience=1,
            length_penalty=1,
            repetition_penalty=1,
            no_repeat_ngram_size=0,
            compression_ratio_threshold=2.4,
            log_prob_threshold=-1.0,
            no_speech_threshold=0.6,
            condition_on_previous_text=True,
            prompt_reset_on_temperature=0.5,
            initial_prompt=None,
            prefix=None,
            suppress_blank=True,
            suppress_tokens=[-1],
            without_timestamps=False,
            max_initial_timestamp=1.0,
            hallucination_silence_threshold=None,
            # 启用进度显示
            log_progress=True,
        )

        # 生成 SRT 格式字幕
        srt_content = ""
        segment_count = 1

        for segment in segments:
            start_time = format_timestamp(segment.start)
            end_time = format_timestamp(segment.end)
            text = segment.text.strip()

            srt_content += f"{segment_count}\n"
            srt_content += f"{start_time} --> {end_time}\n"
            srt_content += f"{text}\n\n"
            segment_count += 1

        # 保存 SRT 文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(srt_content)

        console.print(f"[green]完成[/green] ASR 字幕已生成: {output_file}")
        console.print(f"[info]检测到语言: {info.language} (概率: {info.language_probability:.2f})")

    except Exception as e:
        console.print(f"[red]错误[/red] ASR 处理失败: {e}")
        raise typer.Exit(1)


@app.command("monitor-models")
def monitor_models(
    model_dir: str = typer.Option("./models", "--model-dir", help="模型目录路径"),
    interval: float = typer.Option(2.0, "--interval", help="监控间隔（秒）"),
    duration: int = typer.Option(300, "--duration", help="监控持续时间（秒）"),
):
    """监控模型目录大小变化，检查下载进度。"""
    from rich.live import Live
    from rich.table import Table
    import time
    import shutil

    model_path = Path(model_dir)
    if not model_path.exists():
        console.print(f"[yellow]模型目录不存在: {model_dir}[/yellow]")
        return

    def get_dir_size(path: Path) -> int:
        """获取目录总大小（字节）"""
        total = 0
        for file_path in path.rglob('*'):
            if file_path.is_file():
                total += file_path.stat().st_size
        return total

    def format_size(bytes_size: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_size < 1024.0:
                return ".1f"
            bytes_size /= 1024.0
        return ".1f"

    console.print(f"开始监控模型目录: {model_dir}")
    console.print(f"监控间隔: {interval}秒")
    console.print(f"监控时长: {duration}秒")
    console.print("按 Ctrl+C 停止监控\n")

    start_time = time.time()
    last_size = get_dir_size(model_path)

    try:
        with Live(console=console, refresh_per_second=1) as live:
            while time.time() - start_time < duration:
                current_size = get_dir_size(model_path)
                size_diff = current_size - last_size

                # 创建表格
                table = Table(title=f"模型目录监控 - {model_dir}")
                table.add_column("项目", style="cyan")
                table.add_column("值", style="magenta")

                table.add_row("当前大小", format_size(current_size))
                table.add_row("增长速度", ".1f" if size_diff > 0 else "0 B/s")
                table.add_row("文件数量", str(sum(1 for _ in model_path.rglob('*') if _.is_file())))
                table.add_row("运行时间", ".1f")

                live.update(table)

                last_size = current_size
                time.sleep(interval)

    except KeyboardInterrupt:
        console.print("\n[yellow]监控已停止[/yellow]")

    final_size = get_dir_size(model_path)
    console.print(f"[green]监控完成[/green]")
    console.print(f"最终目录大小: {format_size(final_size)}")


def format_timestamp(seconds: float) -> str:
    """将秒数格式化为 SRT 时间戳格式 (HH:MM:SS,mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int((seconds % 1) * 1000)

    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"


def _parse_srt(path: Path) -> List[dict]:
    """Very small SRT parser returning list of {index,start,end,text} preserving order."""
    text = path.read_text(encoding="utf-8", errors="ignore")
    parts = [p.strip() for p in text.split("\n\n") if p.strip()]
    out: List[dict] = []
    for part in parts:
        lines = part.splitlines()
        if len(lines) < 2:
            continue
        idx = lines[0].strip()
        times = lines[1].strip()
        body = "\n".join(l.strip() for l in lines[2:]).strip()
        if "-->" not in times:
            # malformed; skip
            continue
        start, end = [t.strip() for t in times.split("-->")]
        out.append({"index": idx, "start": start, "end": end, "text": body})
    return out


def _write_srt_entries(path: Path, entries: List[dict]) -> None:
    parts: List[str] = []
    for e in entries:
        parts.append(str(e["index"]))
        parts.append(f"{e['start']} --> {e['end']}")
        parts.append(e["text"])
        parts.append("")  # blank line
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(parts), encoding="utf-8")


# 翻译字幕命令：使用新的翻译子模块
@app.command("translate-subs")
def translate_subs(
    workdir: Path = typer.Option(Path("./work"), "--workdir", "-w", help="工作目录"),
    source: str = typer.Option(None, "--source", "-i", help="输入 SRT 文件（默认 work/subs/asr.en.srt）"),
    lang: str = typer.Option(..., "--lang", "-l", help="目标语言代码，例如 zh-CN"),
    backend: str = typer.Option("deepseek", "--backend", help="翻译后端: deepseek|ollama|openai"),
    api_key: str = typer.Option(None, "--api-key", help="后端 API key（可用环境变量代替）"),
    batch_size: int = typer.Option(30000, "--batch-size", help="每批最大字符数（DeepSeek API 推荐 30000）"),
    force: bool = typer.Option(False, "--force", help="强制覆盖已存在的输出文件"),
    out: str = typer.Option(None, "--out", help="输出 SRT 路径，默认 work/subs/asr.<lang>.srt"),
    no_verify_ssl: bool = typer.Option(False, "--no-verify-ssl", help="禁用SSL证书验证（用于解决SSL连接问题）"),
):
    # Translate SRT subtitles in batches and write translated SRT.
    wp = ensure_workdir(workdir)

    # determine input file
    if source is None:
        input_path = wp.subs_dir / "asr.en.srt"
    else:
        input_path = Path(source)
    if not input_path.exists():
        console.print(f"[red]错误[/red] 未找到输入字幕: {input_path}")
        raise typer.Exit(1)

    # determine output
    if out is None:
        out_path = wp.subs_dir / f"asr.{lang}.srt"
    else:
        out_path = Path(out)
    if out_path.exists() and not force:
        console.print(f"[green]完成[/green] 翻译字幕已存在: {out_path}")
        return

    console.print(f"开始翻译字幕: {input_path} -> {out_path}")
    console.print(f"目标语言: {lang}, 后端: {backend}, batch_size_chars: {batch_size}")
    try:
        translate_srt_file(input_path=input_path, output_path=out_path, target_lang=lang, backend=backend, api_key=api_key, batch_size_chars=batch_size, verify_ssl=not no_verify_ssl)
    except Exception as e:
        console.print(f"[red]错误[/red] 翻译失败: {e}")
        raise typer.Exit(1)

    console.print(f"[green]完成[/green] 翻译字幕: {out_path}")

# end translate-subs
# def translate(
#     workdir: Path = typer.Option(Path("./work"), "--workdir", "-w", help="工作目录"),
#     input_file: str = typer.Option(None, "--input", "-i", help="输入 SRT 文件路径（默认为 work/subs/asr.<source_lang>.srt）"),
#     provider: str = typer.Option("openai", "--provider", help="翻译后端: openai|deepseek|ollama"),
#     model: str = typer.Option(None, "--model", help="后端模型名称（默认按 provider 选择）"),
#     batch_size: int = typer.Option(10, "--batch-size", help="每次翻译的字幕条数"),
#     source_lang: str = typer.Option("en", "--source-lang", help="源语言"),
#     target_lang: str = typer.Option("zh-Hans", "--target-lang", help="目标语言"),
#     force: bool = typer.Option(False, "--force", help="强制重新生成已存在的翻译文件"),
#     debug: bool = typer.Option(False, "--debug", help="启用调试模式，显示详细的 API 响应信息"),
# ):
#     """将 SRT 按批翻译为目标语言，输出到 work/subs/translated.<target>.srt"""
#     wp = ensure_workdir(workdir)

#     # determine input file
#     if input_file is None:
#         input_path = wp.subs_dir / f"asr.{source_lang}.srt"
#     else:
#         input_path = Path(input_file)
#     if not input_path.exists():
#         console.print(f"[red]错误[/red] 未找到输入字幕: {input_path}")
#         raise typer.Exit(1)

#     out_path = wp.translated_sub_srt(target_lang)
#     if out_path.exists() and not force:
#         console.print(f"[green]完成[/green] 翻译字幕已存在: {out_path}")
#         return

#     # choose model defaults
#     if model is None:
#         if provider == "openai":
#             model = "gpt-4"
#         elif provider == "deepseek":
#             model = "deepseek-chat"
#         else:
#             model = "default"

#     # Adjust batch size for different providers
#     if batch_size == 10:  # if using default batch size
#         if provider == "deepseek":
#             batch_size = 5  # DeepSeek seems to have issues with larger batches

#     # build client
#     provider_l = provider.lower()
#     if provider_l == "openai":
#         client = OpenAIClient()
#     elif provider_l == "deepseek":
#         client = DeepseekClient(debug=debug)
#     elif provider_l == "ollama":
#         client = OllamaClient()
#     else:
#         console.print(f"[red]错误[/red] 不支持的 provider: {provider}")
#         raise typer.Exit(1)

#     # parse SRT
#     entries = _parse_srt(input_path)
#     texts = [e["text"] for e in entries]

#     # setup translator
#     cache = TranslationCache(wp.translation_cache)
#     cfg = TranslatorConfig(model=model, source_lang=source_lang, target_lang=target_lang, batch_size=batch_size)
#     translator = SubtitleTranslator(client=client, cache=cache, cfg=cfg)

#     console.print(f"开始翻译 {len(texts)} 条字幕，batch_size={batch_size}，provider={provider}，model={model}")
#     try:
#         translations = translator.translate_texts(texts)
#     except Exception as e:
#         console.print(f"[red]错误[/red] 翻译失败: {e}")
#         raise typer.Exit(1)

#     if len(translations) != len(entries):
#         console.print(f"[red]错误[/red] 翻译结果条目数与原字幕不匹配: {len(translations)} vs {len(entries)}")
#         raise typer.Exit(1)

#     # write translated srt (replace text with translation)
#     new_entries = []
#     for e, tr in zip(entries, translations):
#         new_entries.append({"index": e["index"], "start": e["start"], "end": e["end"], "text": tr})

#     _write_srt_entries(out_path, new_entries)
#     console.print(f"[green]完成[/green] 翻译字幕: {out_path}")

