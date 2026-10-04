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
    subprocess.run(
        [ffmpeg_binary(), "-y", "-f", "concat", "-safe", "0", "-i",
         str(manifest), "-c", "copy", str(output)],
        check=True,
    )
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


def mix_background_music(video: str | Path, narration: str | Path, music: str | Path,
                         output: str | Path, music_volume: float = 0.16) -> Path:
    """Mix narration with looping background music and duck music under narration."""
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    volume = max(0.0, min(float(music_volume), 1.0))
    filter_complex = (
        f"[1:a]volume={volume},aloop=loop=-1:size=2147483647[music];"
        "[music][2:a]sidechaincompress=threshold=0.08:ratio=8:attack=20:release=400[ducked];"
        "[ducked][2:a]amix=inputs=2:duration=first:dropout_transition=2[a]"
    )
    subprocess.run(
        [ffmpeg_binary(), "-y", "-i", str(video), "-i", str(music), "-i", str(narration),
         "-filter_complex", filter_complex, "-map", "0:v:0", "-map", "[a]",
         "-c:v", "copy", "-c:a", "aac", "-shortest", str(output)],
        check=True,
    )
    return output


def burn_subtitles(video: str | Path, subtitles: str | Path, output: str | Path) -> Path:
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    subtitle_path = str(subtitles).replace("\\", "/").replace(":", "\\:")
    subprocess.run(
        [ffmpeg_binary(), "-y", "-i", str(video), "-vf",
         f"subtitles={subtitle_path}", "-c:a", "copy", str(output)],
        check=True,
    )
    return output
