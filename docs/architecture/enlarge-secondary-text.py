"""Enlarge secondary node text in an Arc-rendered SVG.

Arc 0.11.1 fixes node subtitle/description type at 9px with no schema or CLI
option to scale it. After `arc render`, this script bumps every 9px text
(which in our diagram is exactly the set of node subtitles/descriptions) to
a readable size. Run it right after rendering; it is idempotent.

Usage (from repo root):
    python docs/architecture/enlarge-secondary-text.py [path/to/diagram.svg]
"""

from __future__ import annotations

import sys
from pathlib import Path

DEFAULT_SVG = Path(__file__).with_name("entrega1-us5.svg")
FROM_SIZE = 'font-size="9"'
TO_SIZE = 'font-size="11.5"'


def main() -> int:
    svg_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SVG
    text = svg_path.read_text(encoding="utf-8")
    if TO_SIZE in text:
        print(f"already enlarged: {svg_path}")
        return 0
    count = text.count(FROM_SIZE)
    if count == 0:
        print(f"no {FROM_SIZE} texts found in {svg_path}; re-render first?", file=sys.stderr)
        return 1
    svg_path.write_text(text.replace(FROM_SIZE, TO_SIZE), encoding="utf-8")
    print(f"enlarged {count} secondary texts in {svg_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
