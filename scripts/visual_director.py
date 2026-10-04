from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.project import load_project, save_project
from engine.visual_director import apply_visual_specs, build_visual_specs, save_visual_specs


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate cinematic shot specifications for a documentary project.")
    parser.add_argument("--project", required=True, help="Path to project.json")
    args = parser.parse_args()

    project_path = Path(args.project)
    project = load_project(project_path)
    specs = build_visual_specs(project, project_path.parent / "visual-specs.json")
    apply_visual_specs(project, specs)
    save_project(project, project_path)

    print(f"Visual specs: {project_path.parent / 'visual-specs.json'}")
    print(f"Scenes: {len(specs)}")
    print("Mode: " + project.metadata["visual_director"]["mode"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
