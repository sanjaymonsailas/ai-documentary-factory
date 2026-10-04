# Roadmap

## Phase 1 — Working CPU MVP
- [x] Project schema
- [x] Deterministic project generator
- [x] Project validation
- [x] FFmpeg still-to-motion renderer
- [x] Provider-agnostic Kokoro adapter
- [ ] Real research module
- [ ] AI script generation
- [ ] AI storyboard generation
- [ ] Subtitle generation
- [ ] Final timeline assembly

## Phase 2 — Director pipeline
- Research brief → source-backed outline
- Script with scene timing
- Storyboard JSON
- Scene asset manifest
- Automatic asset validation
- Narration + subtitle alignment

## Phase 3 — Visual generation
- Image generation provider interface
- Optional ComfyUI integration
- Blender procedural scenes
- Shot-level camera language
- GPU-only routing for expensive shots

## Phase 4 — Publishing
- Multi-language narration
- Subtitle translation
- Thumbnail generation
- YouTube upload
- Analytics feedback loop

## Design rule

The factory should be able to produce a useful video without requiring a
dedicated GPU. Expensive AI generation is a replaceable renderer, not the core
of the pipeline.
