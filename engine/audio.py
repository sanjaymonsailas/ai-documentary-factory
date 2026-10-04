from __future__ import annotations

import os
import shlex
import subprocess
from pathlib import Path


def synthesize_with_kokoro(text: str, output: str | Path) -> Path:
    """Run a user-provided Kokoro command template.

    Set KOKORO_CMD to a command containing {text} and {output}. This keeps the
    factory independent of a specific Kokoro wrapper/version.
    """
    template = os.getenv("KOKORO_CMD", "").strip()
    if not template:
        raise RuntimeError(
            "KOKORO_CMD is not configured. Add your local Kokoro command template "
            "to .env, for example a wrapper that accepts {text} and {output}."
        )

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    command = template.format(
        text=shlex.quote(text),
        output=shlex.quote(str(output)),
    )
    subprocess.run(command, shell=True, check=True)
    if not output.exists():
        raise RuntimeError(f"Kokoro command completed but produced no file: {output}")
    return output
