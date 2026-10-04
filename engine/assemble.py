from __future__ import annotations

import subprocess
from pathlib import Path

from .video import ffmpeg_binary


def concat_clips(clips: list[Path], output: str | Path) -> Path:
    if not clips:
        raise ValueError("No scene clips to concatenate")
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    manifest = output.parent / "concat.txt"
    manifest.write_text(
        "".join(f"file '{clip.resolve().as_posix()}'\n" for clip in clips),
        encoding="utf-8",
    )
    subprocess.run([ffmpeg_binary(), "-y", "-f", "concat", "-safe", "0", "-i",
                    str(manifest), "-c", "copy", str(output)], check=True)
    return output


def mux_audio(video: str | Path, audio: str | Path, output: str | Path) -> Path:
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [ffmpeg_binary(), "-y", "-i", str(video), "-i", str(audio),
         "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac",
         "-shortest", str(output)],
        check=True,
    )
    return output


def burn_subtitles(video: str | Path, subtitles: str | Path, output: str | Path) -> Path:
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    subtitle_path = str(subtitles).replace("\\", "/").replace(":", "\\:")
    subprocess.run(
        [ffmpeg_binary(), "-y", "-i", str(video), "-vf", f"subtitles={subtitle_path}",
         "-c:a", "copy", str(output)],
        check=True,
    )
    return output
