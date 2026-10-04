from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.ai_research import synthesize_research
from engine.ai_writer import write_script
from engine.director import create_director_project
from engine.research import save_research
from engine.script import build_script_from_project, save_script, save_script_markdown
from engine.storyboard import save_storyboard
from engine.web_research import collect_research
from engine.visual_director import apply_visual_specs, build_visual_specs, save_visual_specs


def main() -> int:
    parser = argparse.ArgumentParser(description="Build an AI-assisted documentary handoff.")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--duration", type=float, default=90)
    parser.add_argument("--language", default="en-us")
    args = parser.parse_args()

    project, project_path, brief_path = create_director_project(
        args.topic, args.duration, args.language, ROOT
    )
    root = project_path.parent

    research = collect_research(args.topic)
    research = synthesize_research(research, root / "research.ai.json")
    save_research(research, root / "research.json")

    script = build_script_from_project(
        project,
        [claim.claim for claim in research.key_claims],
    )
    script = write_script(script, research.to_dict(), root / "script.ai.json")
    save_script(script, root / "script.json")
    save_script_markdown(script, root / "script.md")

    by_id = {scene.id: scene for scene in script.scenes}
    if set(by_id) != {scene.id for scene in project.scenes}:
        raise ValueError("AI script must contain exactly one scene for every director scene")
    for scene in project.scenes:
        scene.narration = by_id[scene.id].narration
    project.metadata["script"] = {
        "version": "1.0",
        "words": script.total_words,
        "words_per_minute": script.words_per_minute,
    }

    specs = build_visual_specs(project, root / "visual-specs.json")
    apply_visual_specs(project, specs)
    save_visual_specs(specs, root / "visual-specs.json")
    save_storyboard(project, root / "storyboard.json")

    print(f"Project:  {project_path}")
    print(f"Research: {root / 'research.json'}")
    print(f"Script:   {root / 'script.json'}")
    print(f"Storyboard: {root / 'storyboard.json'}")
    print("AI providers: " + ("configured" if __import__("os").getenv("AI_RESEARCH_CMD") or __import__("os").getenv("AI_SCRIPT_CMD") else "fallback"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
