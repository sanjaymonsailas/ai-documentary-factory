from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.director import create_director_project
from engine.project import load_project
from engine.storyboard import load_and_validate_storyboard, save_storyboard
from engine.video import render_still


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a CPU-first documentary.")
    parser.add_argument("--project", help="Existing project JSON")
    parser.add_argument("--topic", help="Create a director plan for this topic")
    parser.add_argument("--duration", type=float, default=90)
    parser.add_argument("--language", default="en-us")
    parser.add_argument(
        "--render",
        action="store_true",
        help="Render available scene images into motion clips",
    )
    args = parser.parse_args()

    if not args.project and not args.topic:
        parser.error("provide --project or --topic")

    if args.topic:
        project, project_path, _ = create_director_project(
            args.topic,
            args.duration,
            args.language,
            ROOT,
        )
        storyboard_path = save_storyboard(
            project,
            project_path.parent / "storyboard.json",
        )
        load_and_validate_storyboard(storyboard_path)
    else:
        project_path = Path(args.project)
        project = load_project(project_path)
        storyboard_path = project_path.parent / "storyboard.json"
        if not storyboard_path.exists():
            save_storyboard(project, storyboard_path)
        load_and_validate_storyboard(storyboard_path)

    errors = project.validate()
    if errors:
        raise SystemExit("\n".join(errors))

    print(f"Project:    {project.title}")
    print(f"Duration:   {project.target_duration:.1f}s")
    print(f"Scenes:     {len(project.scenes)}")
    print(f"Storyboard: {storyboard_path}")

    if not args.render:
        print("Director plan ready. Add --render when scene images are available.")
        return 0

    render_dir = project_path.parent / "renders"
    rendered = 0
    for scene in project.scenes:
        image = project_path.parent / "images" / f"{scene.id}.png"
        if not image.exists():
            print(f"SKIP {scene.id}: missing {image}")
            continue
        output = render_dir / f"{scene.id}.mp4"
        render_still(image, output, scene.duration, scene.camera)
        rendered += 1

    print(f"Rendered {rendered}/{len(project.scenes)} scenes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
