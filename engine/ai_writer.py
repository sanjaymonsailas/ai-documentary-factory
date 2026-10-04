from __future__ import annotations

import json
import os
import shlex
import subprocess
from pathlib import Path

from .prompts import SCRIPT_PROMPT
from .script import DocumentaryScript, ScriptScene


def _run(template: str, prompt: str, output: Path) -> None:
    command = template.format(prompt=shlex.quote(prompt), output=shlex.quote(str(output)))
    subprocess.run(command, shell=True, check=True)
    if not output.exists():
        raise RuntimeError(f"AI command completed but produced no file: {output}")


def write_script(script: DocumentaryScript, research: dict, output: str | Path | None = None) -> DocumentaryScript:
    template = os.getenv("AI_SCRIPT_CMD", "").strip()
    if not template:
        return script

    schema = json.dumps(script.to_dict(), ensure_ascii=False, indent=2)
    prompt = (
        SCRIPT_PROMPT
        + "\\nReturn ONLY JSON using this exact script contract. Preserve scene ids, titles and durations.\\n"
        + schema
        + "\\n\\nResearch brief:\\n"
        + json.dumps(research, ensure_ascii=False, indent=2)
    )
    target = Path(output or "/tmp/documentary-script.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    _run(template, prompt, target)
    data = json.loads(target.read_text(encoding="utf-8"))
    result = DocumentaryScript(
        title=data["title"],
        topic=data["topic"],
        language=data.get("language", script.language),
        target_duration=float(data["target_duration"]),
        words_per_minute=int(data.get("words_per_minute", script.words_per_minute)),
        scenes=[ScriptScene(**scene) for scene in data.get("scenes", [])],
        editorial_notes=data.get("editorial_notes", []),
    )
    errors = result.validate()
    if errors:
        raise ValueError("AI script output failed validation:\\n" + "\\n".join(errors))
    return result
