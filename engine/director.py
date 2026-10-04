from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

from .project import save_project
from .schema import Project, Scene


@dataclass(frozen=True)
class DirectorBeat:
    title: str
    purpose: str
    visual_direction: str
    narration_direction: str


DEFAULT_BEATS = (
    DirectorBeat(
        "The hook",
        "Create an immediate curiosity gap.",
        "Open on a visually impossible or intimate image that creates a question.",
        "Start with a short, confident statement or question. Avoid definitions.",
    ),
    DirectorBeat(
        "The mystery",
        "Establish what is surprising and what we do not fully understand.",
        "Move from the human-scale image into an atmospheric or scientific visualization.",
        "Explain the mystery in plain language and raise the stakes.",
    ),
    DirectorBeat(
        "Inside the mechanism",
        "Explain the core process without turning the film into a lecture.",
        "Use macro imagery, diagrams, particles, structures, or procedural 3D.",
        "Use one concrete analogy, then give the factual explanation.",
    ),
    DirectorBeat(
        "The human angle",
        "Make the science emotionally relatable.",
        "Return to a person, memory, environment, or recognizable daily experience.",
        "Connect the mechanism to something the viewer has experienced.",
    ),
    DirectorBeat(
        "The bigger picture",
        "Show the consequence or unresolved question.",
        "Expand the visual scale: city, planet, timeline, network, or abstract system.",
        "Answer 'why should I care?' without exaggeration.",
    ),
    DirectorBeat(
        "The reveal",
        "Deliver the strongest supported insight and leave a memorable final image.",
        "Use the cleanest, most iconic shot of the film with a deliberate camera move.",
        "Resolve the opening question, acknowledge uncertainty where needed, and end cleanly.",
    ),
)


def _duration_weights(count: int) -> list[float]:
    # Hooks and reveals need slightly more room; the middle moves faster.
    weights = [1.15] + [0.92] * (count - 2) + [1.15]
    total = sum(weights)
    return [w / total for w in weights]


def build_director_plan(
    topic: str,
    duration: float = 90,
    language: str = "en-us",
    beats: tuple[DirectorBeat, ...] = DEFAULT_BEATS,
) -> Project:
    if duration <= 0:
        raise ValueError("duration must be greater than zero")
    if not topic.strip():
        raise ValueError("topic must not be empty")

    weights = _duration_weights(len(beats))
    durations = [round(duration * weight, 3) for weight in weights]
    durations[-1] = round(duration - sum(durations[:-1]), 3)

    scenes: list[Scene] = []
    for index, (beat, scene_duration) in enumerate(zip(beats, durations), 1):
        scenes.append(
            Scene(
                id=f"scene_{index:02d}",
                title=beat.title,
                narration=beat.narration_direction,
                duration=scene_duration,
                visual_prompt=(
                    f"{beat.visual_direction} Subject: {topic}. "
                    "Cinematic documentary frame, photorealistic, "
                    "natural materials, atmospheric depth, controlled lighting, "
                    "16:9, no captions, no logos."
                ),
                visual_type="image",
                camera=("slow_zoom" if index in (1, 6) else
                        ("pan_left" if index % 2 else "pan_right")),
                notes=beat.purpose,
            )
        )

    return Project(
        id=_slug(topic),
        title=topic,
        topic=topic,
        language=language,
        target_duration=duration,
        scenes=scenes,
        metadata={
            "stage": "director-plan",
            "director_version": "1.0",
            "beat_count": len(beats),
            "duration_policy": "weighted-hook-and-reveal",
        },
    )


def _slug(value: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "-" for ch in value)
    return "-".join(part for part in cleaned.split("-") if part) or "documentary"


def write_director_brief(project: Project, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        f"# Director Brief — {project.title}",
        "",
        f"**Topic:** {project.topic}",
        f"**Language:** {project.language}",
        f"**Target duration:** {project.target_duration:.1f}s",
        "",
        "## Creative rules",
        "",
        "- Hook before explanation.",
        "- Prefer concrete imagery over generic stock footage.",
        "- One visual idea per shot.",
        "- Keep scientific claims proportional to the evidence.",
        "- Use camera movement deliberately rather than constantly.",
        "- The final image should echo or answer the opening question.",
        "",
        "## Scene plan",
        "",
    ]

    for scene in project.scenes:
        lines.extend(
            [
                f"### {scene.id} — {scene.title}",
                f"- Duration: {scene.duration:.1f}s",
                f"- Camera: {scene.camera}",
                f"- Purpose: {scene.notes}",
                f"- Visual direction: {scene.visual_prompt}",
                f"- Narration direction: {scene.narration}",
                "",
            ]
        )

    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def create_director_project(
    topic: str,
    duration: float = 90,
    language: str = "en-us",
    root: str | Path = ".",
) -> tuple[Project, Path, Path]:
    root = Path(root)
    project = build_director_plan(topic, duration, language)
    project_dir = root / "content" / "projects" / project.id
    project_path = save_project(project, project_dir / "project.json")
    brief_path = write_director_brief(project, project_dir / "director-brief.md")
    return project, project_path, brief_path


__all__ = ["DirectorBeat", "build_director_plan", "create_director_project"]
