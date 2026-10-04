#!/usr/bin/env python3
from pathlib import Path
import argparse, wave
import numpy as np
from kokoro import KPipeline

TEXT = """Every night, when you close your eyes, something strange happens. Your brain builds a world that feels completely real.

You can fall, fly, meet people you have not seen in years, or find yourself somewhere that could never exist.

And yet, while the story feels chaotic, the sleeping brain is not simply switched off. During REM sleep, activity in many brain systems becomes remarkably intense.

Neurons communicate, memories are reactivated, emotions are processed, and pieces of experience are connected in ways we still do not completely understand.

A dream may pull an old face from childhood into a place you visited yesterday. It can blend memories that never belonged together while you were awake.

That strange mixture may help the brain work through emotional experiences and reorganize what happened during the day. The exact purpose is still debated.

Some theories suggest dreams may also let the brain simulate possibilities — rehearsing situations, exploring threats, or simply generating new combinations of ideas.

So why do we dream? There is no single answer yet. And perhaps that is what makes dreams so fascinating: every night, your brain creates a private world, and we are still learning why."""

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",default="output/kokoro-narration.wav")
    p.add_argument("--voice",default="af_heart")
    args=p.parse_args()
    out=Path(args.output); out.parent.mkdir(parents=True,exist_ok=True)
    pipe=KPipeline(lang_code="a")
    with wave.open(str(out),"wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000)
        for r in pipe(TEXT,voice=args.voice,speed=0.96,split_pattern=r"(?<=[.!?])\s+"):
            if r.audio is None: continue
            a=r.audio.detach().cpu().numpy() if hasattr(r.audio,"detach") else np.asarray(r.audio)
            a=np.clip(a,-1,1)
            w.writeframes((a*32767).astype(np.int16).tobytes())
    print(out)
if __name__=="__main__": main()
