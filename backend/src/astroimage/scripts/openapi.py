from __future__ import annotations

import argparse
import json
from pathlib import Path

from astroimage.scripts.paths import backend_root


def cmd_openapi_export(args: argparse.Namespace) -> int:
    from astroimage.main import app

    target = Path(args.output) if args.output else backend_root() / "openapi.json"
    target.write_text(json.dumps(app.openapi(), indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {target}")
    return 0
