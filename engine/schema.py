from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Scene:
    id: str
    title: str
    narration: str
    duration: float
    visual_prompt: str
    visual_type: str = "image"
    camera: str = "slow_zoom"
    notes: str = ""

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.id:
            errors.append("scene.id is required")
        if self.duration <= 0:
            errors.append(f"{self.id}: duration must be > 0")
        if self.visual_type not in {"image", "blender", "graphic", "video"}:
            errors.append(f"{self.id}: unsupported visual_type={self.visual_type}")
        if self.camera not in {"static", "slow_zoom", "pan_left", "pan_right"}:
            errors.append(f"{self.id}: unsupported camera={self.camera}")
        return errors


@dataclass
class Project:
    id: str
    title: str
    topic: str
    language: str
    target_duration: float
    scenes: list[Scene] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.id:
            errors.append("project.id is required")
        if not self.title:
            errors.append("project.title is required")
        if self.target_duration <= 0:
            errors.append("project.target_duration must be > 0")
        seen: set[str] = set()
        for scene in self.scenes:
            if scene.id in seen:
                errors.append(f"duplicate scene id: {scene.id}")
            seen.add(scene.id)
            errors.extend(scene.validate())
        total = sum(scene.duration for scene in self.scenes)
        if self.scenes and abs(total - self.target_duration) > 0.25:
            errors.append(
                f"scene duration total {total:.2f}s does not match "
                f"target {self.target_duration:.2f}s"
            )
        return errors

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
