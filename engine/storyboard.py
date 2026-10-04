from __future__ import annotations

import json
from pathlib import Path

from .schema import Project


def storyboard_from_project(project: Project) -> dict:
    return {
        "version": "1.0",
        "project": {
            "id": project.id,
            "title": project.title,
            "topic": project.topic,
            "language": project.language,
            "duration": project.target_duration,
        },
        "scenes": [
            {
                "id": scene.id,
                "title": scene.title,
                "duration": scene.duration,
                "camera": scene.camera,
                "visual_type": scene.visual_type,
                "visual_prompt": scene.visual_prompt,
                "narration": scene.narration,
                "purpose": scene.notes,
                "asset": {
                    "image": f"images/{scene.id}.png",
                    "video": f"renders/{scene.id}.mp4",
                },
            }
            for scene in project.scenes
        ],
    }


def save_storyboard(project: Project, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(storyboard_from_project(project), indent=2, ensure_ascii=False)
        + "\n",
        encoding="utf-8",
    )
    return path


def validate_storyboard(data: dict) -> list[str]:
    errors: list[str] = []
    if data.get("version") != "1.0":
        errors.append("unsupported storyboard version")
    scenes = data.get("scenes", [])
    if not scenes:
        errors.append("storyboard contains no scenes")

    total = 0.0
    ids: set[str] = set()
    for scene in scenes:
        scene_id = scene.get("id")
        if not scene_id:
            errors.append("scene is missing id")
        elif scene_id in ids:
            errors.append(f"duplicate scene id: {scene_id}")
        else:
            ids.add(scene_id)

        duration = scene.get("duration")
        if not isinstance(duration, (int, float)) or duration <= 0:
            errors.append(f"{scene_id or 'scene'} has invalid duration")
        else:
            total += float(duration)

        if not scene.get("visual_prompt"):
            errors.append(f"{scene_id or 'scene'} is missing visual_prompt")
        if not scene.get("narration"):
            errors.append(f"{scene_id or 'scene'} is missing narration")

    target = data.get("project", {}).get("duration")
    if isinstance(target, (int, float)) and abs(total - float(target)) > 0.25:
        errors.append(f"storyboard duration {total:.2f}s != target {float(target):.2f}s")

    return errors


def load_and_validate_storyboard(path: str | Path) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    errors = validate_storyboard(data)
    if errors:
        raise ValueError("\n".join(errors))
    return data
