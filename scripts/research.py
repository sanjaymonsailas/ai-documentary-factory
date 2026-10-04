from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.research import save_research
from engine.web_research import collect_research


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect external research sources.")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--output")
    parser.add_argument("--wikipedia-limit", type=int, default=5)
    parser.add_argument("--academic-limit", type=int, default=5)
    args = parser.parse_args()

    brief = collect_research(
        args.topic,
        wikipedia_limit=args.wikipedia_limit,
        academic_limit=args.academic_limit,
    )

    output = Path(args.output or f"content/projects/{brief.topic.lower().replace(' ', '-')}/research.json")
    save_research(brief, ROOT / output)

    print(f"Topic:   {brief.topic}")
    print(f"Sources: {len(brief.sources)}")
    print(f"Output:  {output}")
    for source in brief.sources:
        print(f"- {source.publisher}: {source.title}")
    if brief.uncertainties:
        print("Notes:")
        for note in brief.uncertainties:
            print(f"- {note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
