#!/usr/bin/env python3
"""Render a real demo documentary with Kokoro narration and generated cinematic stills.

This is intentionally self-contained for a GitHub-hosted CPU runner. It uses the
legacy Pollinations image endpoint when no image provider is configured, then
renders those shots with FFmpeg and Kokoro.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import textwrap
import urllib.parse
import urllib.request
import wave
from pathlib import Path

SCENES = [
    ("The first world", "A sleeping person in a dark bedroom at 2 AM, moonlight through curtains, intimate cinematic documentary photography, shallow depth of field, 35mm film, no text, no typography"),
    ("A different reality", "A dreamlike human figure falling upward through a vast blue ocean in the sky, fragments of a bedroom floating around them, surreal but photorealistic cinematic VFX, volumetric light, no text"),
    ("The sleeping brain", "Photorealistic human head in profile asleep, translucent glowing brain activity visible inside the skull, scientific documentary visualization blended with live action, dark blue and amber palette, no text"),
    ("REM", "Extreme macro cinematic visualization of biological neurons firing and connecting, warm electrical pulses traveling through branching neural networks, scientific film aesthetic, no text"),
    ("Memory", "A solitary person walking through a dark gallery where fragments of childhood memories appear as floating photographic scenes, emotional cinematic lighting, realistic film still, no text"),
    ("Emotion", "A sleeping face dissolving into symbolic visual memories and emotions, rain, family silhouettes, warm light, subtle surrealism, high-end documentary film still, no text"),
    ("Possibility", "A lone person standing on a mountain above clouds at sunrise while several possible paths appear in the landscape ahead, cinematic epic scale, photorealistic, no text"),
    ("The mystery", "Close-up human eye reflecting stars and a sleeping face, cosmic but realistic, quiet contemplative ending, cinematic 85mm lens, subtle film grain, no text"),
]

NARRATION = [
    "Every night, when you close your eyes, something strange happens. Your brain builds a world that feels completely real.",
    "You can fall, fly, meet people you have not seen in years, or find yourself somewhere that could never exist.",
    "And yet, while the story feels chaotic, the sleeping brain is not simply switched off. During REM sleep, activity in many brain systems becomes remarkably intense.",
    "Neurons communicate, memories are reactivated, emotions are processed, and pieces of experience are connected in ways we still do not completely understand.",
    "A dream may pull an old face from childhood into a place you visited yesterday. It can blend memories that never belonged together while you were awake.",
    "That strange mixture may help the brain work through emotional experiences and reorganize what happened during the day. The exact purpose is still debated.",
    "Some theories suggest dreams may also let the brain simulate possibilities — rehearsing situations, exploring threats, or simply generating new combinations of ideas.",
    "So why do we dream? There is no single answer yet. And perhaps that is what makes dreams so fascinating: every night, your brain creates a private world, and we are still learning why.",
]

def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)

def download_image(prompt: str, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    encoded = urllib.parse.quote(prompt, safe="")
    urls = [
        f"https://image.pollinations.ai/prompt/{encoded}?model=flux&width=1280&height=720&nologo=true",
        f"https://image.pollinations.ai/prompt/{encoded}?model=zimage&width=1280&height=720&nologo=true",
    ]
    last_error = None
    for attempt in range(1, 6):
        for url in urls:
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "ai-documentary-factory/1.0"})
                with urllib.request.urlopen(req, timeout=180) as r:
                    data = r.read()
                if len(data) < 50_000:
                    raise RuntimeError(f"image response too small: {len(data)} bytes")
                output.write_bytes(data)
                return
            except Exception as exc:
                last_error = exc
                print(f"image attempt {attempt} failed: {exc}")
        import time
        time.sleep(min(30, 4 * attempt))
    raise RuntimeError(f"could not generate image after retries: {last_error}")

def generate_kokoro(text: str, output: Path, voice: str = "af_heart") -> None:
    from kokoro import KPipeline
    import numpy as np

    output.parent.mkdir(parents=True, exist_ok=True)
    pipeline = KPipeline(lang_code="a")
    with wave.open(str(output), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(24000)
        for result in pipeline(text, voice=voice, speed=0.96, split_pattern=r"(?<=[.!?])\s+"):
            if result.audio is None:
                continue
            audio = result.audio.detach().cpu().numpy() if hasattr(result.audio, "detach") else np.asarray(result.audio)
            audio = np.clip(audio, -1.0, 1.0)
            wav_file.writeframes((audio * 32767).astype(np.int16).tobytes())

def make_scene(image: Path, duration: float, output: Path, mode: int) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    # Alternate subtle push-ins and lateral moves. The image itself contains no captions.
    if mode % 3 == 0:
        crop = "scale=1600:-2,crop=1280:720:(in_w-1280)/2:(in_h-720)/2"
        vf = f"{crop},zoompan=z='min(zoom+0.0009,1.08)':d=1:s=1280x720:fps=24"
    elif mode % 3 == 1:
        vf = "scale=1600:-2,crop=1280:720:(in_w-1280)/2:(in_h-720)/2,zoompan=z='min(zoom+0.0007,1.06)':x='(iw-ow)*on/(60*24)':d=1:s=1280x720:fps=24"
    else:
        vf = "scale=1600:-2,crop=1280:720:(in_w-1280)/2:(in_h-720)/2,zoompan=z='min(zoom+0.0008,1.07)':x='(iw-ow)*(1-on/(60*24))':d=1:s=1280x720:fps=24"
    run(["ffmpeg", "-y", "-loop", "1", "-i", str(image), "-vf", vf, "-t", f"{duration:.3f}", "-r", "24", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an", str(output)])

def concat(files: list[Path], output: Path) -> None:
    manifest = output.parent / "concat.txt"
    manifest.write_text("".join(f"file '{p.resolve()}'\n" for p in files))
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(manifest), "-c", "copy", str(output)])

def srt_time(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def write_srt(durations: list[float], output: Path) -> None:
    lines=[]
    t=0.0
    for i, ((title, _), narration, dur) in enumerate(zip(SCENES, NARRATION, durations), 1):
        lines += [str(i), f"{srt_time(t)} --> {srt_time(t+dur)}", narration, ""]
        t += dur
    output.write_text("\n".join(lines), encoding="utf-8")

def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--output", default="output/why-humans-dream-kokoro.mp4")
    parser.add_argument("--voice", default="af_heart")
    args=parser.parse_args()

    root=Path(args.output).resolve().parent
    images=root/"images"
    clips=root/"clips"
    root.mkdir(parents=True, exist_ok=True)

    # Keep pacing documentary-like: roughly 8–10 seconds per beat.
    durations=[8.0,8.5,8.0,8.5,9.0,9.0,9.0,10.0]
    for i, ((title,prompt), dur) in enumerate(zip(SCENES,durations),1):
        img=images/f"scene_{i:02d}.jpg"
        if not img.exists():
            print(f"Generating visual {i}: {title}")
            download_image(prompt, img)

    narration_text=" ".join(NARRATION)
    voice=root/"narration.wav"
    print("Generating Kokoro narration...")
    generate_kokoro(narration_text, voice, args.voice)

    scene_clips=[]
    for i, dur in enumerate(durations,1):
        clip=clips/f"scene_{i:02d}.mp4"
        make_scene(images/f"scene_{i:02d}.jpg", dur, clip, i)
        scene_clips.append(clip)

    silent=root/"silent.mp4"
    concat(scene_clips, silent)
    srt=root/"subtitles.srt"
    write_srt(durations, srt)

    # A restrained ambient bed synthesized locally; narration remains dominant.
    music=root/"ambient.wav"
    run(["ffmpeg","-y","-f","lavfi","-i","sine=frequency=110:sample_rate=24000:duration=72","-af","volume=0.035,lowpass=f=900,afade=t=in:st=0:d=5,afade=t=out:st=65:d=7",str(music)])

    mixed=root/"mixed.mp4"
    run(["ffmpeg","-y","-i",str(silent),"-i",str(voice),"-i",str(music),"-filter_complex","[2:a]volume=0.12[m];[1:a][m]amix=inputs=2:duration=first:dropout_transition=2[a]","-map","0:v","-map","[a]","-c:v","copy","-c:a","aac","-b:a","192k","-shortest",str(mixed)])

    final=Path(args.output).resolve()
    subtitle_filter=f"subtitles={srt.as_posix()}:force_style='FontName=DejaVu Sans,FontSize=18,PrimaryColour=&H00FFFFFF,OutlineColour=&H80000000,BorderStyle=1,Outline=2,Shadow=1,MarginV=36,Alignment=2'"
    run(["ffmpeg","-y","-i",str(mixed),"-vf",subtitle_filter,"-c:v","libx264","-crf","18","-preset","medium","-c:a","copy","-movflags","+faststart",str(final)])
    print(final)

if __name__ == "__main__":
    main()
