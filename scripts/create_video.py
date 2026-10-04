from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.project import load_project
from engine.video import render_still


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a CPU-first documentary.")
    parser.add_argument("--project", help="Existing project JSON")
    parser.add_argument("--topic", help="Create a starter project for this topic")
    parser.add_argument("--duration", type=float, default=90)
    parser.add_argument("--render", action="store_true", help="Render available scene images")
    args = parser.parse_args()

    if not args.project and not args.topic:
        parser.error("provide --project or --topic")

    if args.project:
        project_path = Path(args.project)
    else:
        from scripts.create_project import build_project
        project = build_project(args.topic, args.duration, "en-us")
        project_path = ROOT / f"content/projects/{project.id}/project.json"
        project_path.parent.mkdir(parents=True, exist_ok=True)
        project_path.write_text(
            json.dumps(project.to_dict(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    project = load_project(project_path)
    errors = project.validate()
    if errors:
        raise SystemExit("\n".join(errors))

    print(f"Project: {project.title}")
    print(f"Duration: {project.target_duration:.1f}s")
    print(f"Scenes: {len(project.scenes)}")

    if not args.render:
        print("Storyboard/project ready. Pass --render when scene images are available.")
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
