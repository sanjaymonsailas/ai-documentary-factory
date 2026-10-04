# AI Documentary Factory

A CPU-first, cloud-ready production pipeline for turning a documentary topic into a structured story, research package, cinematic scene assets, narration, subtitles, music and a final video.

## Philosophy

**AI is the director's assistant, not the infrastructure requirement.**

The factory is provider-agnostic: CPU fallbacks work without a GPU, while image/video/voice providers can be plugged in through command templates.

## Production pipeline

```
Topic
  ↓
Live source collection
  ↓
Research + claims
  ↓
AI writer
  ↓
Visual director
  ↓
Storyboard JSON
  ↓
Image/video scene generation
  ↓
Kokoro narration
  ↓
Music + ducking
  ↓
FFmpeg assembly
  ↓
Subtitles
  ↓
Final documentary
```

## Rendering

CPU-only still motion:
```bash
python scripts/render_factory.py --project content/projects/why-humans-dream/project.json --audio --subtitles
```

With background music:
```bash
python scripts/render_factory.py --project content/projects/why-humans-dream/project.json --music assets/music/bed.wav --subtitles
```

AI video scenes can be enabled with `--ai-video` when `DOCUMENTARY_VIDEO_CMD` is configured. The command may use:
- `{prompt}`
- `{output}`
- `{duration}`
- `{image}` (optional first-frame/reference image)

Example provider templates belong in local environment configuration; no vendor is hard-coded into the factory.

## Environment

- `DOCUMENTARY_IMAGE_CMD` — image generator command with `{prompt}` and `{output}`
- `DOCUMENTARY_VIDEO_CMD` — optional video generator command with `{prompt}`, `{output}`, `{duration}`, `{image}`
- `KOKORO_CMD` — narration command with `{text}` and `{output}`
- `DOCUMENTARY_FONT` — optional subtitle/fallback font

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python scripts/ai_pipeline.py --topic "Why humans dream" --duration 90 --language en-us
python scripts/render_factory.py --project content/projects/why-humans-dream/project.json --audio --subtitles
```

The research collector uses public Wikipedia and OpenAlex endpoints without a paid API key. **Source collection is not fact verification**; claims still require synthesis and review.

## Repository layout

- `engine/` — reusable production engine
- `scripts/` — command-line entry points
- `content/` — documentary projects and source material
- `blender/` — optional procedural 3D renderer
- `assets/` — generated/local assets
- `output/` — final renders
- `.github/workflows/` — automated validation

## First target

A repeatable 60–90 second documentary from one topic, then 5–10 minute documentaries and multilingual versions.
