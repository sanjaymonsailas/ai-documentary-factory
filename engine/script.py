from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .schema import Project


@dataclass
class ScriptScene:
    id: str
    title: str
    duration: float
    narration: str
    target_words: int
    source_refs: list[str] = field(default_factory=list)

    @property
    def word_count(self) -> int:
        return len(re.findall(r"\b[\w'’-]+\b", self.narration))

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.id:
            errors.append("script scene id is required")
        if self.duration <= 0:
            errors.append(f"{self.id}: duration must be > 0")
        if not self.narration.strip():
            errors.append(f"{self.id}: narration is empty")
        if self.target_words <= 0:
            errors.append(f"{self.id}: target_words must be > 0")
        return errors


@dataclass
class DocumentaryScript:
    title: str
    topic: str
    language: str
    target_duration: float
    words_per_minute: int = 145
    scenes: list[ScriptScene] = field(default_factory=list)
    editorial_notes: list[str] = field(default_factory=list)

    def validate(self) -> list[str]:
        errors: list[str] = []
        seen: set[str] = set()
        total_duration = 0.0

        if self.target_duration <= 0:
            errors.append("target_duration must be > 0")
        if not 100 <= self.words_per_minute <= 190:
            errors.append("words_per_minute should normally be between 100 and 190")

        for scene in self.scenes:
            errors.extend(scene.validate())
            if scene.id in seen:
                errors.append(f"duplicate script scene id: {scene.id}")
            seen.add(scene.id)
            total_duration += scene.duration

        if self.scenes and abs(total_duration - self.target_duration) > 0.25:
            errors.append(
                f"script duration {total_duration:.2f}s != target {self.target_duration:.2f}s"
            )
        return errors

    @property
    def total_words(self) -> int:
        return sum(scene.word_count for scene in self.scenes)

    @property
    def target_total_words(self) -> int:
        return round(self.target_duration / 60 * self.words_per_minute)

    def to_dict(self) -> dict:
        return asdict(self)


def _word_target(duration: float, words_per_minute: int) -> int:
    return max(8, round(duration / 60 * words_per_minute))


def build_script_from_project(
    project: Project,
    research_claims: list[str] | None = None,
    words_per_minute: int = 145,
) -> DocumentaryScript:
    """Create a safe draft script contract.

    This is intentionally deterministic. An LLM can replace the narration later,
    but the timing and structure remain validated by the engine.
    """
    claims = research_claims or []
    scenes: list[ScriptScene] = []

    for index, scene in enumerate(project.scenes):
        target = _word_target(scene.duration, words_per_minute)

        if index == 0:
            narration = (
                f"What if the answer to {project.topic.lower()} is stranger "
                "than we think? "
                "Before we explain it, let's look at what we actually know."
            )
        elif index == len(project.scenes) - 1:
            narration = (
                f"So what does this tell us about {project.topic.lower()}? "
                "The strongest answer is not a simple one. "
                "The evidence gives us a clearer picture, while some questions remain open."
            )
        elif claims:
            claim = claims[min(index - 1, len(claims) - 1)]
            narration = (
                f"Here is the key idea: {claim} "
                "The important part is what the evidence can actually support."
            )
        else:
            narration = (
                f"This is where {project.topic.lower()} becomes interesting. "
                "The evidence points to a mechanism, but the details deserve a closer look."
            )

        scenes.append(
            ScriptScene(
                id=scene.id,
                title=scene.title,
                duration=scene.duration,
                narration=narration,
                target_words=target,
            )
        )

    script = DocumentaryScript(
        title=project.title,
        topic=project.topic,
        language=project.language,
        target_duration=project.target_duration,
        words_per_minute=words_per_minute,
        scenes=scenes,
        editorial_notes=[
            "This is an AI-assisted draft and must be checked against research before publication.",
            "Do not present hypotheses as established facts.",
            "Replace generic narration with source-backed claims during the AI writing stage.",
        ],
    )
    return script


def save_script(script: DocumentaryScript, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(script.to_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return path


def save_script_markdown(script: DocumentaryScript, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# Script — {script.title}",
        "",
        f"**Topic:** {script.topic}",
        f"**Language:** {script.language}",
        f"**Target duration:** {script.target_duration:.1f}s",
        f"**Target pace:** {script.words_per_minute} words/minute",
        "",
    ]

    for scene in script.scenes:
        lines.extend(
            [
                f"## {scene.id} — {scene.title}",
                f"*{scene.duration:.1f}s · target {scene.target_words} words*",
                "",
                scene.narration,
                "",
            ]
        )

    if script.editorial_notes:
        lines.extend(["## Editorial notes", ""])
        lines.extend(f"- {note}" for note in script.editorial_notes)

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def load_script(path: str | Path) -> DocumentaryScript:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    scenes = [ScriptScene(**scene) for scene in data.get("scenes", [])]
    script = DocumentaryScript(
        title=data["title"],
        topic=data["topic"],
        language=data.get("language", "en-us"),
        target_duration=float(data["target_duration"]),
        words_per_minute=int(data.get("words_per_minute", 145)),
        scenes=scenes,
        editorial_notes=data.get("editorial_notes", []),
    )
    errors = script.validate()
    if errors:
        raise ValueError("\n".join(errors))
    return script


__all__ = [
    "DocumentaryScript",
    "ScriptScene",
    "build_script_from_project",
    "load_script",
    "save_script",
    "save_script_markdown",
]
