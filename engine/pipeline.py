from __future__ import annotations

from pathlib import Path

from .director import create_director_project
from .research import ResearchBrief, ResearchClaim, save_research
from .script import build_script_from_project, save_script, save_script_markdown
from .storyboard import save_storyboard


def build_draft_pipeline(
    topic: str,
    duration: float = 90,
    language: str = "en-us",
    root: str | Path = ".",
) -> dict[str, Path]:
    root = Path(root)
    project, project_path, brief_path = create_director_project(topic, duration, language, root)
    project_dir = project_path.parent
    storyboard_path = save_storyboard(project, project_dir / "storyboard.json")

    research = ResearchBrief(
        topic=topic,
        question=f"What is the most evidence-backed explanation for {topic.lower()}?",
        key_claims=[
            ResearchClaim(
                id="claim_01",
                claim="Replace this draft claim with a source-backed finding before publication.",
                confidence="needs-review",
            )
        ],
        uncertainties=["This research handoff has not yet been verified by an external research agent."],
        sources=[],
    )
    research_path = project_dir / "research.json"
    save_research(research, research_path)

    script = build_script_from_project(
        project,
        research_claims=[claim.claim for claim in research.key_claims],
    )
    script_path = save_script(script, project_dir / "script.json")
    script_markdown_path = save_script_markdown(script, project_dir / "script.md")

    return {
        "project": project_path,
        "director_brief": brief_path,
        "research": research_path,
        "storyboard": storyboard_path,
        "script": script_path,
        "script_markdown": script_markdown_path,
    }
