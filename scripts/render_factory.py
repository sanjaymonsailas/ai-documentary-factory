from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.assets import generate_scene_image
from engine.assemble import burn_subtitles, concat_clips, mix_background_music, mux_audio
from engine.audio import synthesize_with_kokoro
from engine.project import load_project
from engine.storyboard import load_and_validate_storyboard
from engine.subtitles import write_srt
from engine.video import render_ai_video, render_still


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a documentary from a storyboard.")
    parser.add_argument("--project", required=True)
    parser.add_argument("--audio", action="store_true")
    parser.add_argument("--subtitles", action="store_true")
    parser.add_argument("--music", help="Background music file; narration is automatically ducked over it.")
    parser.add_argument("--ai-video", action="store_true",
                        help="Use DOCUMENTARY_VIDEO_CMD for scenes whose visual_type is video.")
    args = parser.parse_args()

    project_path = Path(args.project)
    project = load_project(project_path)
    root = project_path.parent
    storyboard = load_and_validate_storyboard(root / "storyboard.json")

    image_dir, render_dir, output_dir = root / "images", root / "renders", root / "output"
    for directory in (image_dir, render_dir, output_dir):
        directory.mkdir(exist_ok=True)

    clips: list[Path] = []
    for scene in storyboard["scenes"]:
        image = image_dir / f"{scene['id']}.png"
        if not image.exists():
            generate_scene_image(scene["visual_prompt"], image, scene["title"])

        clip = render_dir / f"{scene['id']}.mp4"
        if args.ai_video and scene.get("visual_type") == "video":
            render_ai_video(scene["visual_prompt"], clip, float(scene["duration"]), image)
        else:
            render_still(image, clip, float(scene["duration"]), scene.get("camera", "slow_zoom"))
        clips.append(clip)

    silent = output_dir / "documentary-silent.mp4"
    concat_clips(clips, silent)
    srt = output_dir / "subtitles.srt"
    write_srt(storyboard["scenes"], srt)

    final = silent
    narration_file = None
    if args.audio or args.music:
        narration = " ".join(scene["narration"] for scene in storyboard["scenes"])
        narration_file = output_dir / "voice.wav"
        synthesize_with_kokoro(narration, narration_file)
        if args.music:
            mixed = output_dir / "documentary-mix.mp4"
            mix_background_music(final, narration_file, Path(args.music), mixed)
            final = mixed
        else:
            with_audio = output_dir / "documentary-audio.mp4"
            mux_audio(final, narration_file, with_audio)
            final = with_audio

    if args.subtitles:
        subtitled = output_dir / "final.mp4"
        burn_subtitles(final, srt, subtitled)
        final = subtitled

    print(f"Final video: {final}")
    print(f"Subtitles: {srt}")
    print(f"Scenes: {len(clips)}")
    if not narration_file:
        print("Audio: skipped (use --audio or --music with KOKORO_CMD configured)")
    if args.ai_video:
        print("AI video: enabled for storyboard scenes marked visual_type=video")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
