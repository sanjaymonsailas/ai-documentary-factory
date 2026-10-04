from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.assets import generate_scene_image
from engine.assemble import burn_subtitles, concat_clips, mux_audio
from engine.audio import synthesize_with_kokoro
from engine.project import load_project
from engine.storyboard import load_and_validate_storyboard
from engine.subtitles import write_srt
from engine.video import render_still


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a documentary from a storyboard.")
    parser.add_argument("--project", required=True)
    parser.add_argument("--audio", action="store_true")
    parser.add_argument("--subtitles", action="store_true")
    args = parser.parse_args()

    project_path = Path(args.project)
    project = load_project(project_path)
    root = project_path.parent
    storyboard = load_and_validate_storyboard(root / "storyboard.json")

    image_dir = root / "images"
    render_dir = root / "renders"
    output_dir = root / "output"
    for directory in (image_dir, render_dir, output_dir):
        directory.mkdir(exist_ok=True)

    clips: list[Path] = []
    for scene in storyboard["scenes"]:
        image = image_dir / f"{scene['id']}.png"
        if not image.exists():
            generate_scene_image(scene["visual_prompt"], image, scene["title"])
        clip = render_dir / f"{scene['id']}.mp4"
        render_still(image, clip, float(scene["duration"]), scene.get("camera", "slow_zoom"))
        clips.append(clip)

    silent = output_dir / "documentary-silent.mp4"
    concat_clips(clips, silent)

    srt = output_dir / "subtitles.srt"
    write_srt(storyboard["scenes"], srt)

    final = silent
    if args.audio:
        narration = " ".join(scene["narration"] for scene in storyboard["scenes"])
        voice = output_dir / "voice.wav"
        synthesize_with_kokoro(narration, voice)
        with_audio = output_dir / "documentary-audio.mp4"
        mux_audio(final, voice, with_audio)
        final = with_audio

    if args.subtitles:
        subtitled = output_dir / "final.mp4"
        burn_subtitles(final, srt, subtitled)
        final = subtitled

    print(f"Final video: {final}")
    print(f"Subtitles: {srt}")
    print(f"Scenes: {len(clips)}")
    if not args.audio:
        print("Audio: skipped (use --audio with KOKORO_CMD configured)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
