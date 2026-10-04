from __future__ import annotations

import os
import shlex
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def _font(size: int):
    candidates = [
        os.getenv("DOCUMENTARY_FONT", ""),
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def generate_fallback_image(prompt: str, output: str | Path, title: str = "") -> Path:
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    w, h = 1920, 1080
    image = Image.new("RGB", (w, h))
    px = image.load()
    seed = sum(ord(c) for c in prompt) % 255
    for y in range(h):
        for x in range(w):
            t = (x / w) * 0.55 + (y / h) * 0.45
            px[x, y] = (int(8 + 24 * t), int(12 + 18 * (1 - t)), int(22 + 42 * ((x + seed) % w) / w))
    draw = ImageDraw.Draw(image, "RGBA")
    draw.rectangle((0, h * 0.68, w, h), fill=(0, 0, 0, 150))
    if title:
        draw.text((90, h - 190), title, font=_font(64), fill=(245, 245, 245, 235))
    draw.text((90, h - 105), "AI DOCUMENTARY FACTORY • FALLBACK FRAME",
              font=_font(28), fill=(190, 200, 215, 210))
    image.save(output, quality=94)
    return output


def generate_scene_image(prompt: str, output: str | Path, title: str = "") -> Path:
    template = os.getenv("DOCUMENTARY_IMAGE_CMD", "").strip()
    if template:
        output = Path(output)
        output.parent.mkdir(parents=True, exist_ok=True)
        command = template.format(prompt=shlex.quote(prompt), output=shlex.quote(str(output)))
        subprocess.run(command, shell=True, check=True)
        if not output.exists():
            raise RuntimeError(f"Image command completed but produced no file: {output}")
        return output
    return generate_fallback_image(prompt, output, title)
