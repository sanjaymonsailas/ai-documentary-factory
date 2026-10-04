# Rendering

The factory is CPU-first and can run end-to-end without a GPU.

## Scene images

If DOCUMENTARY_IMAGE_CMD is not configured, the factory creates deterministic cinematic fallback frames. This keeps CI and local pipeline testing reproducible.

For a real local image model, set DOCUMENTARY_IMAGE_CMD to a command containing {prompt} and {output}. The command must create the requested image.

## Render

    python scripts/render_factory.py --project content/projects/why-humans-dream/project.json

This creates scene images, FFmpeg motion clips, subtitles, and a silent MP4.

## Kokoro

Set KOKORO_CMD to a wrapper containing {text} and {output}, then run:

    python scripts/render_factory.py --project content/projects/why-humans-dream/project.json --audio --subtitles

No paid API is required by the core factory.

## Flow

storyboard.json -> image adapter -> CPU FFmpeg motion -> Kokoro -> SRT -> final.mp4
