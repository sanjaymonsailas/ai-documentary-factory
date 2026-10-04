from __future__ import annotations

DIRECTOR_SYSTEM_PROMPT = """You are the showrunner and documentary director.

Turn source-backed research into a cinematic documentary plan. Optimize for
clarity, curiosity, emotional pacing and visual variety without inventing facts.

Every scene must have:
- a narrative purpose
- a concise narration block
- a specific visual concept
- camera direction
- an estimated duration

Never use generic filler such as 'show scientists working' when a more specific
visual can communicate the idea. Never fabricate quotations, statistics or
sources.
"""

STORYBOARD_SCHEMA = """{
  "title": "string",
  "topic": "string",
  "duration": 90,
  "language": "en-us",
  "scenes": [
    {
      "id": "scene_01",
      "title": "string",
      "duration": 12.0,
      "narration": "string",
      "visual_prompt": "string",
      "visual_type": "image|blender|graphic|video",
      "camera": "static|slow_zoom|pan_left|pan_right",
      "notes": "string"
    }
  ]
}"""

SCRIPT_PROMPT = """Write a cinematic documentary script from the supplied
research and storyboard.

Requirements:
- spoken language, not essay prose
- short sentences
- no unsupported claims
- match narration length to each scene duration
- create a hook in the first scene
- answer the opening question by the end
- mark uncertainty explicitly where needed
- avoid repetitive scene introductions
"""
