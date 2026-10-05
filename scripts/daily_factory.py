#!/usr/bin/env python3
import argparse, json, os, subprocess, time, urllib.parse, urllib.request, wave
from datetime import date
from pathlib import Path
import numpy as np
from kokoro import KPipeline

ROOT=Path(__file__).resolve().parents[1]
LOGO=ROOT/"brand"/"logo.jpg"

def run(cmd):
    subprocess.run(cmd, check=True)

def api(payload):
    req=urllib.request.Request("https://gen.pollinations.ai/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Authorization":"Bearer "+os.environ["POLLINATIONS_API_KEY"],"Content-Type":"application/json"},
        method="POST")
    with urllib.request.urlopen(req,timeout=180) as r: return json.loads(r.read())

def topic_for(day):
    topics=json.loads((ROOT/"content/daily_topics.json").read_text())
    return topics[day.toordinal()%len(topics)]

def write_script(topic):
    prompt=("Create an 8-12 minute English cinematic documentary for ITS ALL GOOD MAN about "+topic+
            ". Use a strong hook, escalating curiosity, clear explanations, human examples, a surprising insight and a memorable ending. "
            "Avoid fake quotes, invented statistics and unsupported claims. Return ONLY JSON with title, description, tags and scenes. "
            "Create 18-22 scenes. Each scene needs narration of 50-90 spoken words, a detailed photorealistic cinematic visual_prompt with no text, and a purpose. Target 1200-1600 words.")
    result=api({"model":os.getenv("TEXT_MODEL","openai/gpt-5.4-nano"),
                "messages":[{"role":"user","content":prompt}],"temperature":0.7})
    raw=result["choices"][0]["message"]["content"].strip()
    raw=raw.replace(chr(96)*3+"json","").replace(chr(96)*3,"").strip()
    a,b=raw.find("{"),raw.rfind("}")
    if a<0 or b<=a: raise RuntimeError("Model did not return JSON")
    doc=json.loads(raw[a:b+1])
    if len(doc.get("scenes",[]))<16: raise RuntimeError("Too few scenes")
    return doc

def image(prompt,out,seed):
    model=os.getenv("IMAGE_MODEL","black-forest-labs/flux.1-schnell")
    text=prompt+", cinematic documentary still, photorealistic, subtle film grain, no text, no logo"
    url=("https://gen.pollinations.ai/image/"+urllib.parse.quote(text,safe="")+
         "?model="+urllib.parse.quote(model)+"&width=1280&height=720&seed="+str(seed))
    last=None
    for n in range(5):
        try:
            req=urllib.request.Request(url,headers={"Authorization":"Bearer "+os.environ["POLLINATIONS_API_KEY"]})
            with urllib.request.urlopen(req,timeout=180) as r: data=r.read()
            if len(data)<30000: raise RuntimeError("small image")
            out.write_bytes(data); return
        except Exception as e:
            last=e; time.sleep(3*(n+1))
    raise RuntimeError("image failed: "+str(last))

def voice(text,out,pipe):
    with wave.open(str(out),"wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000)
        for r in pipe(text,voice=os.getenv("KOKORO_VOICE","af_heart"),speed=0.96):
            if r.audio is None: continue
            x=r.audio.detach().cpu().numpy() if hasattr(r.audio,"detach") else np.asarray(r.audio)
            x=np.clip(x,-1,1); w.writeframes((x*32767).astype(np.int16).tobytes())

def wav_len(p):
    with wave.open(str(p)) as w: return w.getnframes()/w.getframerate()

def srt_time(x):
    ms=int(x*1000); h,ms=divmod(ms,3600000); m,ms=divmod(ms,60000); s,ms=divmod(ms,1000)
    return "%02d:%02d:%02d,%03d"%(h,m,s,ms)

def write_srt(scenes,p):
    t=0; lines=[]
    for i,x in enumerate(scenes,1):
        lines += [str(i),srt_time(t)+" --> "+srt_time(t+x["duration"]),x["narration"],""]
        t+=x["duration"]
    p.write_text("\n".join(lines),encoding="utf-8")

def scene(img,aud,out):
    d=wav_len(aud)
    motion="zoompan=z='min(zoom+0.0006,1.075)':d=1:s=1280x720:fps=24"
    vf="scale=1600:-2,crop=1280:720:(in_w-1280)/2:(in_h-720)/2,"+motion
    run(["ffmpeg","-y","-loop","1","-i",str(img),"-i",str(aud),"-vf",vf,"-t","%.3f"%d,
         "-r","24","-c:v","libx264","-crf","20","-preset","veryfast","-pix_fmt","yuv420p",
         "-c:a","aac","-b:a","160k","-shortest",str(out)])
    return d

def concat(files,out):
    m=out.parent/(out.stem+"_list.txt")
    m.write_text("".join(["file '"+str(x.resolve())+"'\n" for x in files]))
    run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(m),"-c","copy",str(out)])

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--topic"); p.add_argument("--date"); p.add_argument("--output",default="output/daily")
    a=p.parse_args()
    day=date.fromisoformat(a.date) if a.date else date.today()
    topic=a.topic or topic_for(day)
    root=Path(a.output)/day.isoformat()
    images,audios,clips=root/"images",root/"audio",root/"clips"
    for x in (images,audios,clips): x.mkdir(parents=True,exist_ok=True)

    doc=write_script(topic)
    pipe=KPipeline(lang_code="a")
    scenes=[]
    for i,src in enumerate(doc["scenes"],1):
        img=images/("%02d.jpg"%i); aud=audios/("%02d.wav"%i); clip=clips/("%02d.mp4"%i)
        if not img.exists(): image(src["visual_prompt"],img,1000+i)
        if not aud.exists(): voice(src["narration"],aud,pipe)
        x=dict(src); x["duration"]=scene(img,aud,clip); scenes.append(x)

    doc["scenes"]=scenes
    (root/"script.json").write_text(json.dumps(doc,indent=2,ensure_ascii=False),encoding="utf-8")
    write_srt(scenes,root/"subtitles.srt")
    silent=root/"silent.mp4"; concat(sorted(clips.glob("*.mp4")),silent)

    am=root/"audio_list.txt"
    am.write_text("".join(["file '"+str(x.resolve())+"'\n" for x in sorted(audios.glob("*.wav"))]))
    narration=root/"narration.wav"
    run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(am),"-c","copy",str(narration)])

    music=root/"ambient.wav"
    run(["ffmpeg","-y","-f","lavfi","-i","sine=frequency=92:sample_rate=24000:duration=900",
         "-af","volume=0.025,lowpass=f=500,afade=t=in:st=0:d=8,afade=t=out:st=820:d=40",str(music)])

    mixed=root/"mixed.mp4"
    run(["ffmpeg","-y","-i",str(silent),"-i",str(narration),"-i",str(music),
         "-filter_complex","[2:a]volume=0.10[m];[1:a][m]amix=inputs=2:duration=first:dropout_transition=2[a]",
         "-map","0:v","-map","[a]","-c:v","copy","-c:a","aac","-b:a","192k","-shortest",str(mixed)])

    final=root/"final.mp4"
    style="FontName=DejaVu Sans,FontSize=17,PrimaryColour=&H00FFFFFF,OutlineColour=&H90000000,BorderStyle=1,Outline=2,Shadow=1,MarginV=34,Alignment=2"
    filt="[1:v]scale=105:-1,format=rgba,colorchannelmixer=aa=0.86[logo];[0:v][logo]overlay=W-w-28:H-h-28,subtitles="+str(root/"subtitles.srt")+":force_style='"+style+"'"
    run(["ffmpeg","-y","-i",str(mixed),"-i",str(LOGO),"-filter_complex",filt,
         "-c:v","libx264","-crf","19","-preset","medium","-c:a","copy","-movflags","+faststart",str(final)])

    meta={"topic":topic,"title":doc["title"],"description":doc["description"],"tags":doc.get("tags",[]),"date":day.isoformat()}
    (root/"metadata.json").write_text(json.dumps(meta,indent=2),encoding="utf-8")
    print("FINAL",final)

if __name__=="__main__":
    main()
