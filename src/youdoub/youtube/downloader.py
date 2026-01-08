from __future__ import annotations

import json
from pathlib import Path
import yt_dlp


class MetadataJSONEncoder(json.JSONEncoder):
    """自定义 JSON 编码器，用于处理 yt-dlp 元数据对象。"""

    def default(self, obj):
        # 处理 yt-dlp 后处理对象
        if hasattr(obj, '__class__') and obj.__class__.__module__.startswith('yt_dlp'):
            # 为 yt-dlp 对象返回字符串表示
            return f"<{obj.__class__.__name__}>"

        # 处理其他不可序列化的对象
        try:
            return super().default(obj)
        except TypeError:
            return str(obj)




def download_youtube_video(*, url: str, video_out: Path, meta_out: Path, force: bool = False, download_subs: bool = True, sub_lang: str = "en", keep_separate_streams: bool = False) -> None:
    """下载 YouTube 视频（合并的）、元数据和字幕。

    使用 yt-dlp Python API。

    参数:
        url: YouTube 视频 URL
        video_out: 视频文件输出路径
        meta_out: 元数据 JSON 输出路径
        force: 强制重新下载，即使文件已存在
        download_subs: 是否下载字幕
        sub_lang: 字幕语言（默认：'en'）
        keep_separate_streams: 是否保留单独的音频和视频流文件
    """
    video_out.parent.mkdir(parents=True, exist_ok=True)

    # 检查需要下载的内容
    need_video = not video_out.exists() or force
    need_meta = not meta_out.exists() or force
    need_subs = False

    if download_subs:
        subs_dir = video_out.parent / "subs"
        subs_dir.mkdir(parents=True, exist_ok=True)
        sub_files = [
            subs_dir / f"source.{sub_lang}.srt",
            subs_dir / f"source.{sub_lang}.vtt"
        ]
        need_subs = not any(sub_file.exists() for sub_file in sub_files) or force

    # 如果不需要下载任何内容，跳过
    if not need_video and not need_meta and not need_subs:
        print("所有必需文件已存在，跳过下载")
        return

    # Prepare subtitle directory if needed
    subs_dir = video_out.parent / "subs"
    if download_subs:
        subs_dir.mkdir(parents=True, exist_ok=True)

    # 配置 yt-dlp 选项
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',  # 优先选择广泛兼容的格式
        'merge_output_format': 'mp4',
        'nopart': True,  # 避免中断时留下 .part 文件
        'remote_components': ['ejs:github', 'ejs:npm'],  # 必需的远程组件（列表形式）
        'quiet': True,  # 抑制控制台输出
        'no_warnings': False,  # 显示警告
        # 网络和 SSL 选项，用于处理连接问题
        'retries': 10,  # 增加重试次数
        'fragment_retries': 10,  # 分片重试次数
        'retry_sleep': 2,  # 重试间隔时间
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        },
    }

    # 如果保留单独流，添加相应选项
    if keep_separate_streams:
        ydl_opts.update({
            'keepvideo': True,  # 保留视频流文件
            'keepaudio': True,  # 保留音频流文件
        })

    # 如果需要，添加字幕选项
    if download_subs:
        ydl_opts.update({
            'writesubtitles': True,           # 下载人工字幕
            'writeautomaticsub': True,        # 下载自动生成的字幕
            'subtitleslangs': [sub_lang],     # 字幕语言
            'subtitlesformat': 'srt',         # 字幕格式
        })

    # 设置输出模板（必须在字幕选项之后）
    if download_subs:
        ydl_opts['outtmpl'] = {
            'default': str(video_out),    # 视频输出
            'subtitle': str(subs_dir / f'source.{sub_lang}.%(ext)s'),  # 字幕输出
        }
    else:
        ydl_opts['outtmpl'] = str(video_out)  # 仅视频输出

    print(f"使用 yt-dlp Python API 下载: {url}")
    print(f"输出: {video_out}")

    try:
        # 下载视频（以及需要的字幕和流文件）
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            # 保存元数据
            meta_out.write_text(json.dumps(info, ensure_ascii=False, indent=2, cls=MetadataJSONEncoder), encoding="utf-8")
            print(f"成功下载视频和元数据")
            if download_subs and need_subs:
                print(f"成功下载字幕")
            if keep_separate_streams:
                print(f"保留了单独的音频和视频流文件")

    except yt_dlp.DownloadError as e:
        print(f"下载失败: {e}")
        # 回退：尝试在不下载的情况下获取元数据
        try:
            with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                fallback_meta = {
                    "webpage_url": url,
                    "_warning": f"视频下载失败: {e}",
                    "_fallback_metadata": True,
                    **info
                }
                meta_out.write_text(json.dumps(fallback_meta, ensure_ascii=False, indent=2, cls=MetadataJSONEncoder), encoding="utf-8")
                print("保存了回退元数据（未下载视频）")
        except Exception as meta_e:
            print(f"元数据提取也失败了: {meta_e}")
            fallback_meta = {
                "webpage_url": url,
                "_warning": f"下载和元数据提取都失败了。下载错误: {e}，元数据错误: {meta_e}",
                "_yt_dlp_python_api": True,
            }
            meta_out.write_text(json.dumps(fallback_meta, ensure_ascii=False, indent=2, cls=MetadataJSONEncoder), encoding="utf-8")
            print("保存了最小回退元数据")

