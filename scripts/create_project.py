from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.project import save_project
from engine.schema import Project, Scene


def slugify(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower())
    return value.strip("-") or "documentary"


def build_project(topic: str, duration: float, language: str) -> Project:
    # Deterministic starter structure. The director/storyboard stage can replace
    # these scenes with researched content later.
    scene_count = 6 if duration <= 120 else 10
    base = duration / scene_count
    scenes = []

    beats = [
        ("The hook", "Open with a striking question or contradiction."),
        ("The mystery", "Introduce the central mystery and why it matters."),
        ("The mechanism", "Explain the core mechanism in simple visual terms."),
        ("The human angle", "Connect the idea to real human experience."),
        ("The bigger picture", "Show the wider implication or consequence."),
        ("The reveal", "End with the strongest insight and a memorable final image."),
    ]

    for index in range(scene_count):
        title, note = beats[index % len(beats)]
        scene_id = f"scene_{index + 1:02d}"
        scenes.append(
            Scene(
                id=scene_id,
                title=title,
                narration=f"[DRAFT NARRATION] {note}",
                duration=round(base, 3),
                visual_prompt=(
                    f"Cinematic documentary visualization about {topic}; "
                    f"{note.lower()}; photorealistic, atmospheric lighting, "
                    "strong composition, no text, 16:9"
                ),
                visual_type="image",
                camera=["slow_zoom", "pan_left", "pan_right"][index % 3],
                notes=note,
            )
        )

    # Make the sum exact after rounding.
    scenes[-1].duration = round(
        duration - sum(scene.duration for scene in scenes[:-1]), 3
    )

    return Project(
        id=slugify(topic),
        title=topic,
        topic=topic,
        language=language,
        target_duration=duration,
        scenes=scenes,
        metadata={
            "stage": "starter",
            "pipeline": "cpu-first",
            "created_by": "ai-documentary-factory",
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a documentary project skeleton.")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--duration", type=float, default=90)
    parser.add_argument("--language", default="en-us")
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    project = build_project(args.topic, args.duration, args.language)
    errors = project.validate()
    if errors:
        raise SystemExit("\n".join(errors))

    output = Path(args.output or f"content/projects/{project.id}/project.json")
    save_project(project, ROOT / output)
    print(f"Created {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
