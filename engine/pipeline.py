from __future__ import annotations

from pathlib import Path

from .director import create_director_project
from .research import save_research
from .script import build_script_from_project, save_script, save_script_markdown
from .storyboard import save_storyboard
from .web_research import collect_research


def build_draft_pipeline(
    topic: str,
    duration: float = 90,
    language: str = "en-us",
    root: str | Path = ".",
    collect_web_sources: bool = True,
) -> dict[str, Path]:
    """Build a documentary production handoff.

    Web source collection is enabled by default and uses public APIs that do not
    require a paid key. It collects evidence candidates; it does not fabricate
    verified claims.
    """
    root = Path(root)
    project, project_path, brief_path = create_director_project(
        topic, duration, language, root
    )
    project_dir = project_path.parent

    storyboard_path = save_storyboard(project, project_dir / "storyboard.json")

    if collect_web_sources:
        research = collect_research(topic)
    else:
        from .research import ResearchBrief, ResearchClaim
        research = ResearchBrief(
            topic=topic,
            question=f"What is the best evidence-backed explanation for {topic.lower()}?",
            key_claims=[
                ResearchClaim(
                    id="claim_01",
                    claim="Replace this draft claim with a source-backed finding before publication.",
                    confidence="needs-review",
                )
            ],
            uncertainties=["Web collection was disabled."],
            sources=[],
        )

    research_path = project_dir / "research.json"
    save_research(research, research_path)

    claim_text = [claim.claim for claim in research.key_claims]
    script = build_script_from_project(project, research_claims=claim_text)
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
