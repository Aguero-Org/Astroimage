import json
from pathlib import Path

from astroimage.main import app


def main() -> None:
    target = Path(__file__).resolve().parents[1] / "openapi.json"
    target.write_text(json.dumps(app.openapi(), indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {target}")


if __name__ == "__main__":
    main()
