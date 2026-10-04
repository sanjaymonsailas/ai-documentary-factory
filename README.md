# AI Documentary Factory

A CPU-first, cloud-ready production pipeline for turning a documentary topic into a structured story, research package, generated visuals, narration, subtitles and a final video.

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
Live source collection
  ↓
Research package
  ↓
Script
  ↓
Director
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

python scripts/pipeline.py \
  --topic "Why humans dream" \
  --duration 90
```

This now collects real candidate sources from public Wikipedia and OpenAlex endpoints without requiring a paid API key. **Source collection is not the same as fact verification**: the next AI research stage will inspect those sources and turn them into claims with citations and caveats.

## Research contract

Every factual claim should eventually contain:
- confidence level
- source references
- caveat where appropriate

The factory never intentionally invents citations, statistics or quotations.

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
1. source-backed research
2. timed script
3. storyboard JSON
4. scene visuals
5. Kokoro narration
6. subtitles
7. assembled MP4

After that works reliably, we scale to 5–10 minute documentaries and multilingual versions.
