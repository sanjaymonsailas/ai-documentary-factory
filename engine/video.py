from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def ffmpeg_binary() -> str:
    binary = shutil.which("ffmpeg")
    if not binary:
        raise RuntimeError(
            "ffmpeg was not found. Install FFmpeg and ensure it is on PATH."
        )
    return binary


def render_still(
    image: str | Path,
    output: str | Path,
    duration: float,
    camera: str = "slow_zoom",
    fps: int = 24,
) -> Path:
    """Turn one 16:9 still into a lightweight motion clip.

    This intentionally uses FFmpeg's CPU filters rather than an AI video model,
    making the MVP runnable without a GPU.
    """
    image = Path(image)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)

    zoom = {
        "static": "zoompan=z=1.0",
        "slow_zoom": "zoompan=z='min(zoom+0.0007,1.12)'",
        "pan_left": "zoompan=z='min(zoom+0.0004,1.08)':x='iw*0.08*(1-on/((duration)*25))'",
        "pan_right": "zoompan=z='min(zoom+0.0004,1.08)':x='iw*0.08*(on/((duration)*25))'",
    }.get(camera, "zoompan=z='min(zoom+0.0007,1.12)'")

    command = [
        ffmpeg_binary(),
        "-y",
        "-loop",
        "1",
        "-i",
        str(image),
        "-vf",
        f"scale=1920:1080:force_original_aspect_ratio=increase,"
        f"crop=1920:1080,{zoom}:d={max(1, int(duration * fps))}:s=1920x1080:fps={fps}",
        "-t",
        str(duration),
        "-r",
        str(fps),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        str(output),
    ]

    subprocess.run(command, check=True)
    return output
