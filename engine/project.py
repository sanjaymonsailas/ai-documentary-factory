from __future__ import annotations

import json
from pathlib import Path

from .schema import Project, Scene


def project_from_dict(data: dict) -> Project:
    scenes = [Scene(**scene) for scene in data.get("scenes", [])]
    return Project(
        id=data["id"],
        title=data["title"],
        topic=data["topic"],
        language=data.get("language", "en-us"),
        target_duration=float(data["target_duration"]),
        scenes=scenes,
        metadata=data.get("metadata", {}),
    )


def save_project(project: Project, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(project.to_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return path


def load_project(path: str | Path) -> Project:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return project_from_dict(data)
