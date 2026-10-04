from __future__ import annotations

import argparse
import sys

from .project import load_project


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a documentary project JSON.")
    parser.add_argument("project", help="Path to project JSON")
    args = parser.parse_args()

    project = load_project(args.project)
    errors = project.validate()
    if errors:
        print("INVALID")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"VALID: {project.title}")
    print(f"Scenes: {len(project.scenes)}")
    print(f"Duration: {project.target_duration:.2f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
