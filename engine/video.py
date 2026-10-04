from __future__ import annotations

import os
import shlex
import shutil
import subprocess
from pathlib import Path


def ffmpeg_binary() -> str:
    binary = shutil.which("ffmpeg")
    if not binary:
        raise RuntimeError("ffmpeg was not found. Install FFmpeg and ensure it is on PATH.")
    return binary


def render_still(image: str | Path, output: str | Path, duration: float,
                 camera: str = "slow_zoom", fps: int = 24) -> Path:
    """Turn a still into a reliable CPU video clip.

    The first factory smoke test intentionally uses a conservative renderer:
    motion can be added by providers later, while the baseline must work on
    every GitHub-hosted FFmpeg build.
    """
    image = Path(image)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        ffmpeg_binary(), "-y", "-loop", "1", "-i", str(image),
        "-vf", "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080",
        "-t", str(max(0.1, duration)), "-r", str(fps),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        str(output),
    ]
    subprocess.run(command, check=True)
    return output


def render_ai_video(prompt: str, output: str | Path, duration: float,
                    image: str | Path | None = None) -> Path:
    """Run an optional AI/video provider command.

    DOCUMENTARY_VIDEO_CMD may contain {prompt}, {output}, {duration}, and
    {image}. The adapter is provider-agnostic; without it callers should use
    the CPU still renderer instead.
    """
    template = os.getenv("DOCUMENTARY_VIDEO_CMD", "").strip()
    if not template:
        raise RuntimeError(
            "DOCUMENTARY_VIDEO_CMD is not configured; use the CPU still renderer "
            "or configure an AI video provider command."
        )
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    command = template.format(
        prompt=shlex.quote(prompt),
        output=shlex.quote(str(output)),
        duration=shlex.quote(str(duration)),
        image=shlex.quote(str(image)) if image else "''",
    )
    subprocess.run(command, shell=True, check=True)
    if not output.exists():
        raise RuntimeError(f"Video command completed but produced no file: {output}")
    return output
