from __future__ import annotations

from pathlib import Path


def _timestamp(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    hours, ms = divmod(ms, 3_600_000)
    minutes, ms = divmod(ms, 60_000)
    secs, ms = divmod(ms, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"


def write_srt(scenes: list[dict], output: str | Path) -> Path:
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    cursor = 0.0
    for index, scene in enumerate(scenes, 1):
        duration = float(scene["duration"])
        text = " ".join(str(scene.get("narration", "")).split())
        lines.extend([str(index), f"{_timestamp(cursor)} --> {_timestamp(cursor + duration)}", text, ""])
        cursor += duration
    output.write_text("\n".join(lines), encoding="utf-8")
    return output
