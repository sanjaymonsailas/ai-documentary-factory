from __future__ import annotations

import json
import os
import shlex
import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .schema import Project, Scene


@dataclass
class VisualSpec:
    scene_id: str
    shot: str
    subject: str
    environment: str
    composition: str
    lens: str
    lighting: str
    palette: str
    camera: str
    asset_type: str = "image"
    continuity_keys: list[str] = field(default_factory=list)
    negative_prompt: str = "text, captions, logos, watermarks, UI, distorted anatomy, duplicate subjects"
    prompt: str = ""


def _fallback_spec(scene: Scene, topic: str, index: int) -> VisualSpec:
    lenses = ["24mm wide", "35mm cinematic", "50mm natural", "85mm intimate"]
    compositions = [
        "strong foreground subject with layered depth and negative space",
        "center-weighted hero composition with environmental context",
        "macro detail framed against a soft atmospheric background",
        "human-scale composition with a clear visual focal point",
    ]
    lights = [
        "soft directional light",
        "moody volumetric light",
        "natural dawn light",
        "controlled studio-like contrast",
    ]
    lens = lenses[(index - 1) % len(lenses)]
    composition = compositions[(index - 1) % len(compositions)]
    lighting = lights[(index - 1) % len(lights)]
    shot = f"{scene.title}: a cinematic documentary shot about {topic}, {scene.visual_prompt}"
    prompt = (
        f"{shot} Composition: {composition}. Lens: {lens}. Lighting: {lighting}. "
        "Color palette: restrained charcoal, warm natural tones where relevant, subtle cool highlights. "
        "Photorealistic, physically plausible materials, atmospheric perspective, high detail, "
        "cinematic production design, 16:9. No text, captions, logos or watermarks."
    )
    return VisualSpec(
        scene_id=scene.id,
        shot=shot,
        subject=topic,
        environment="documentary-realistic environment appropriate to the subject",
        composition=composition,
        lens=lens,
        lighting=lighting,
        palette="restrained neutrals with subtle cool highlights",
        camera=scene.camera,
        continuity_keys=[topic.lower(), "documentary-world", scene.title.lower()],
        prompt=prompt,
    )


def _run(template: str, prompt: str, output: Path) -> None:
    command = template.format(prompt=shlex.quote(prompt), output=shlex.quote(str(output)))
    subprocess.run(command, shell=True, check=True)
    if not output.exists():
        raise RuntimeError(f"visual director command completed but produced no file: {output}")


def build_visual_specs(project: Project, output: str | Path | None = None) -> list[VisualSpec]:
    template = os.getenv("VISUAL_DIRECTOR_CMD", "").strip()
    fallback = [_fallback_spec(scene, project.topic, i) for i, scene in enumerate(project.scenes, 1)]
    if not template:
        return fallback

    target = Path(output or "/tmp/visual-specs.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    contract = {
        "project": {
            "title": project.title,
            "topic": project.topic,
            "language": project.language,
            "duration": project.target_duration,
        },
        "scenes": [asdict(spec) for spec in fallback],
        "requirements": [
            "Preserve scene_id and return exactly one spec per scene.",
            "Make prompts concrete and filmable rather than abstract.",
            "Keep recurring subjects, locations and visual motifs consistent.",
            "Use realistic lens, lighting, composition and camera language.",
            "Do not add text, logos, captions or watermarks.",
        ],
    }
    _run(template, json.dumps(contract, ensure_ascii=False, indent=2), target)
    data = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("visual director output must be a JSON array")

    by_id = {scene.id: scene for scene in project.scenes}
    fallback_by_id = {spec.scene_id: spec for spec in fallback}
    specs: list[VisualSpec] = []
    for item in data:
        if not isinstance(item, dict):
            raise ValueError("visual director scene must be an object")
        scene_id = item.get("scene_id")
        if scene_id not in by_id:
            raise ValueError(f"unknown visual scene id: {scene_id}")
        base = fallback_by_id[scene_id]
        spec = VisualSpec(**{**asdict(base), **item, "scene_id": scene_id})
        if not spec.prompt.strip():
            raise ValueError(f"{scene_id}: visual prompt is empty")
        specs.append(spec)

    if {s.scene_id for s in specs} != set(by_id) or len(specs) != len(by_id):
        raise ValueError("visual director output must contain exactly one spec per scene")
    return specs


def apply_visual_specs(project: Project, specs: list[VisualSpec]) -> Project:
    by_id = {spec.scene_id: spec for spec in specs}
    for scene in project.scenes:
        spec = by_id[scene.id]
        scene.visual_prompt = spec.prompt
        scene.camera = spec.camera
        scene.visual_type = spec.asset_type
    project.metadata["visual_director"] = {
        "version": "1.0",
        "mode": "configured" if os.getenv("VISUAL_DIRECTOR_CMD", "").strip() else "fallback",
        "continuity": [
            {"scene_id": spec.scene_id, "keys": spec.continuity_keys}
            for spec in specs
        ],
    }
    return project


def save_visual_specs(specs: list[VisualSpec], path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps([asdict(spec) for spec in specs], indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return path
