from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class ResearchSource:
    id: str
    title: str
    url: str
    publisher: str = ""
    accessed_at: str = ""
    source_type: str = "web"
    notes: str = ""

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.id:
            errors.append("research source id is required")
        if not self.title:
            errors.append(f"{self.id}: source title is required")
        if not self.url:
            errors.append(f"{self.id}: source url is required")
        return errors


@dataclass
class ResearchClaim:
    id: str
    claim: str
    confidence: str = "needs-review"
    source_refs: list[str] = field(default_factory=list)
    caveat: str = ""

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.id:
            errors.append("research claim id is required")
        if not self.claim:
            errors.append(f"{self.id}: claim is empty")
        if self.confidence not in {"established", "supported", "needs-review", "hypothesis"}:
            errors.append(f"{self.id}: invalid confidence={self.confidence}")
        return errors


@dataclass
class ResearchBrief:
    topic: str
    question: str
    key_claims: list[ResearchClaim] = field(default_factory=list)
    uncertainties: list[str] = field(default_factory=list)
    sources: list[ResearchSource] = field(default_factory=list)

    def validate(self) -> list[str]:
        errors: list[str] = []
        source_ids = {source.id for source in self.sources}
        for source in self.sources:
            errors.extend(source.validate())
        for claim in self.key_claims:
            errors.extend(claim.validate())
            for ref in claim.source_refs:
                if ref not in source_ids:
                    errors.append(f"{claim.id}: unknown source reference {ref}")
            if claim.confidence in {"established", "supported"} and not claim.source_refs:
                errors.append(f"{claim.id}: supported claims require source references")
        return errors

    def to_dict(self) -> dict:
        return asdict(self)


def save_research(brief: ResearchBrief, path: str | Path) -> Path:
    errors = brief.validate()
    if errors:
        raise ValueError("\n".join(errors))
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(brief.to_dict(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def load_research(path: str | Path) -> ResearchBrief:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    brief = ResearchBrief(
        topic=data["topic"],
        question=data["question"],
        key_claims=[ResearchClaim(**x) for x in data.get("key_claims", [])],
        uncertainties=data.get("uncertainties", []),
        sources=[ResearchSource(**x) for x in data.get("sources", [])],
    )
    errors = brief.validate()
    if errors:
        raise ValueError("\n".join(errors))
    return brief


def research_prompt(topic: str) -> str:
    return f"""You are the research producer for a cinematic documentary.

Topic: {topic}

Return ONLY valid JSON matching the repository research contract.

Rules:
1. Prefer primary sources, universities, scientific journals, government agencies,
   museums and reputable reference organizations.
2. Never invent citations, URLs, quotations or statistics.
3. Every established/supported claim must reference at least one source.
4. Separate observations from interpretations and hypotheses.
5. Add caveats when a claim is context-dependent.
6. Avoid sensational wording.
"""


__all__ = ["ResearchBrief", "ResearchClaim", "ResearchSource", "load_research", "research_prompt", "save_research"]
