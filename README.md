# AI Documentary Factory

A CPU-first, cloud-ready production pipeline for turning a documentary topic into a structured story, generated visuals, narration, subtitles and a final video.

## Philosophy

**AI is the director's assistant, not the infrastructure requirement.**

The first version deliberately avoids requiring:
- a personal VPS
- a dedicated GPU
- paid video-generation APIs
- paid voice APIs

FFmpeg handles deterministic video assembly, while Kokoro can provide local voice synthesis. Blender is optional for procedural 3D scenes.

## Current pipeline

```
Topic
  ↓
Project schema
  ↓
Research
  ↓
Script
  ↓
Storyboard JSON
  ↓
Scene assets
  ↓
Kokoro narration
  ↓
FFmpeg assembly
  ↓
Final documentary
```

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python scripts/create_project.py \
  --topic "Why humans dream" \
  --duration 90

python -m engine.validate \
  content/projects/why-humans-dream/project.json

python scripts/create_video.py \
  --project content/projects/why-humans-dream/project.json
```

The current CLI creates and validates the production plan. Scene generation, research and final timeline assembly are being added incrementally.

## Repository layout

- `engine/` — reusable production engine
- `scripts/` — command-line entry points
- `content/` — documentary projects and source material
- `blender/` — optional procedural 3D renderer
- `assets/` — generated/local assets
- `output/` — final renders
- `.github/workflows/` — automated validation

## First target

A repeatable 60–90 second documentary from one topic, with:
1. researched outline
2. timed script
3. storyboard JSON
4. scene visuals
5. Kokoro narration
6. subtitles
7. assembled MP4

After that works reliably, we scale to 5–10 minute documentaries and multilingual versions.
