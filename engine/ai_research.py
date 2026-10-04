from __future__ import annotations

import json
import os
import shlex
import subprocess
from pathlib import Path

from .prompts import RESEARCH_SCHEMA, RESEARCH_SYSTEM_PROMPT
from .research import ResearchBrief, ResearchClaim, ResearchSource


def _run(template: str, prompt: str, output: Path) -> None:
    command = template.format(prompt=shlex.quote(prompt), output=shlex.quote(str(output)))
    subprocess.run(command, shell=True, check=True)
    if not output.exists():
        raise RuntimeError(f"AI command completed but produced no file: {output}")


def _fallback(brief: ResearchBrief) -> ResearchBrief:
    claims: list[ResearchClaim] = []
    for index, source in enumerate(brief.sources[:5], 1):
        if source.notes.strip():
            claims.append(
                ResearchClaim(
                    id=f"claim_{index:02d}",
                    claim=source.notes.strip().replace("\n", " ")[:500],
                    confidence="needs-review",
                    source_refs=[source.id],
                    caveat="Generated from a source summary and requires editorial verification.",
                )
            )
    brief.key_claims = claims
    brief.uncertainties.append(
        "No AI research provider was configured; fallback claims are source summaries, not verified conclusions."
    )
    return brief


def synthesize_research(brief: ResearchBrief, output: str | Path | None = None) -> ResearchBrief:
    template = os.getenv("AI_RESEARCH_CMD", "").strip()
    if not template:
        return _fallback(brief)

    prompt = (
        RESEARCH_SYSTEM_PROMPT
        + "\\nReturn ONLY JSON matching this schema:\\n"
        + RESEARCH_SCHEMA
        + "\\n\\nTopic:\\n" + brief.topic
        + "\\nQuestion:\\n" + brief.question
        + "\\n\\nCandidate sources:\\n"
        + json.dumps([source.__dict__ for source in brief.sources], ensure_ascii=False, indent=2)
    )
    target = Path(output or "/tmp/documentary-research.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    _run(template, prompt, target)
    data = json.loads(target.read_text(encoding="utf-8"))
    result = ResearchBrief(
        topic=data["topic"],
        question=data["question"],
        key_claims=[ResearchClaim(**x) for x in data.get("key_claims", [])],
        uncertainties=data.get("uncertainties", []),
        sources=[ResearchSource(**x) for x in data.get("sources", [])],
    )
    errors = result.validate()
    if errors:
        raise ValueError("AI research output failed validation:\\n" + "\\n".join(errors))
    return result
