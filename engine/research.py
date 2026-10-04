from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class ResearchSource:
    title: str
    url: str
    publisher: str = ""
    accessed_at: str = ""
    notes: str = ""


@dataclass
class ResearchBrief:
    topic: str
    question: str
    key_claims: list[str] = field(default_factory=list)
    uncertainties: list[str] = field(default_factory=list)
    sources: list[ResearchSource] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def save_research(brief: ResearchBrief, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(brief.to_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return path


def research_prompt(topic: str) -> str:
    return f"""You are the research producer for a cinematic documentary.

Topic: {topic}

Return a concise, source-backed research brief in JSON with:
- question
- key_claims: 5-10 factual claims
- uncertainties: claims that need qualification
- sources: title, url, publisher, accessed_at, notes

Rules:
1. Prefer primary sources, universities, scientific journals, government agencies,
   museums, and reputable reference organizations.
2. Do not invent citations.
3. Separate established findings from hypotheses.
4. Avoid sensational wording.
5. Every important factual claim should map to at least one source.
"""


__all__ = ["ResearchBrief", "ResearchSource", "research_prompt", "save_research"]
