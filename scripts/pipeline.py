from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.pipeline import build_draft_pipeline


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a complete documentary production handoff.")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--duration", type=float, default=90)
    parser.add_argument("--language", default="en-us")
    args = parser.parse_args()

    outputs = build_draft_pipeline(args.topic, args.duration, args.language, ROOT)
    for name, path in outputs.items():
        print(f"{name:18} {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
