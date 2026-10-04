from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from typing import Any

from .research import ResearchBrief, ResearchClaim, ResearchSource


USER_AGENT = "ai-documentary-factory/0.1 (+https://github.com/sanjaymonsailas/ai-documentary-factory)"


def _get_json(url: str, timeout: int = 15) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _slug(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return value or "source"


def _wikipedia_search(topic: str, limit: int = 5) -> list[ResearchSource]:
    params = urllib.parse.urlencode(
        {
            "action": "query",
            "list": "search",
            "srsearch": topic,
            "format": "json",
            "utf8": 1,
            "srlimit": limit,
        }
    )
    data = _get_json(f"https://en.wikipedia.org/w/api.php?{params}")
    sources: list[ResearchSource] = []

    for index, item in enumerate(data.get("query", {}).get("search", []), 1):
        title = item.get("title", "")
        url = "https://en.wikipedia.org/wiki/" + urllib.parse.quote(
            title.replace(" ", "_")
        )
        sources.append(
            ResearchSource(
                id=f"wiki_{index:02d}",
                title=title,
                url=url,
                publisher="Wikipedia",
                source_type="encyclopedia",
                notes=re.sub("<[^>]+>", "", item.get("snippet", "")),
            )
        )
    return sources


def _openalex_search(topic: str, limit: int = 5) -> list[ResearchSource]:
    params = urllib.parse.urlencode(
        {
            "search": topic,
            "per-page": limit,
        }
    )
    data = _get_json(f"https://api.openalex.org/works?{params}")
    sources: list[ResearchSource] = []

    for index, work in enumerate(data.get("results", []), 1):
        title = work.get("display_name") or work.get("title") or "Untitled work"
        doi = work.get("doi")
        url = doi or work.get("id") or ""
        if not url:
            continue

        primary = work.get("primary_location") or {}
        source = primary.get("source") or {}
        abstract = _abstract_from_inverted_index(work.get("abstract_inverted_index"))
        publisher = source.get("display_name") or "OpenAlex"

        sources.append(
            ResearchSource(
                id=f"paper_{index:02d}",
                title=title,
                url=url,
                publisher=publisher,
                source_type="academic-paper",
                notes=abstract[:900],
            )
        )
    return sources


def _abstract_from_inverted_index(value: Any) -> str:
    if not isinstance(value, dict):
        return ""
    words: list[tuple[int, str]] = []
    for word, positions in value.items():
        if not isinstance(positions, list):
            continue
        for position in positions:
            if isinstance(position, int):
                words.append((position, word))
    words.sort(key=lambda item: item[0])
    return " ".join(word for _, word in words)


def collect_research(
    topic: str,
    wikipedia_limit: int = 5,
    academic_limit: int = 5,
) -> ResearchBrief:
    """Collect real external source records without requiring a paid API key.

    This stage intentionally collects evidence candidates rather than pretending
    that snippets are verified conclusions. An AI research/writer stage can then
    read these source records and turn them into source-backed claims.
    """
    errors: list[str] = []
    sources: list[ResearchSource] = []

    try:
        sources.extend(_wikipedia_search(topic, wikipedia_limit))
    except Exception as exc:
        errors.append(f"Wikipedia collection failed: {exc}")

    try:
        sources.extend(_openalex_search(topic, academic_limit))
    except Exception as exc:
        errors.append(f"OpenAlex collection failed: {exc}")

    deduped: list[ResearchSource] = []
    seen_urls: set[str] = set()
    for source in sources:
        if source.url and source.url not in seen_urls:
            seen_urls.add(source.url)
            deduped.append(source)

    brief = ResearchBrief(
        topic=topic,
        question=f"What is the best evidence-backed explanation for {topic.lower()}?",
        key_claims=[],
        uncertainties=(
            ["Source collection completed; claims still require synthesis and verification."]
            + errors
        ),
        sources=deduped,
    )
    return brief


__all__ = ["collect_research"]
