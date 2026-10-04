from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.director import create_director_project
from engine.storyboard import save_storyboard


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a cinematic documentary director plan."
    )
    parser.add_argument("--topic", required=True)
    parser.add_argument("--duration", type=float, default=90)
    parser.add_argument("--language", default="en-us")
    args = parser.parse_args()

    project, project_path, brief_path = create_director_project(
        args.topic,
        args.duration,
        args.language,
        ROOT,
    )
    storyboard_path = save_storyboard(
        project,
        project_path.parent / "storyboard.json",
    )

    print(f"Project:    {project_path}")
    print(f"Director:   {brief_path}")
    print(f"Storyboard: {storyboard_path}")
    print(f"Scenes:     {len(project.scenes)}")
    print(f"Duration:   {project.target_duration:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
