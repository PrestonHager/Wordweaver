# scripts/update_icons.py
#
# Download the Lucide icons the app uses into src/icons/lucide/.
# Only the icons listed here are kept, so add a name to ICONS when you need a new one.
# Run it from the repo root with `uv run python scripts/update_icons.py`.
# You can find icon names at https://lucide.dev/icons.

import sys
import urllib.request
from pathlib import Path

LUCIDE_VERSION = "1.73.0"
BASE_URL = f"https://unpkg.com/lucide-static@{LUCIDE_VERSION}"

ICONS = [
    "audio-lines",
    "book-open",
    "check",
    "chevron-down",
    "clipboard-paste",
    "copy",
    "external-link",
    "file-plus",
    "folder-open",
    "info",
    "layout-dashboard",
    "log-out",
    "moon",
    "pencil",
    "plus",
    "save",
    "save-all",
    "sun",
    "trash-2",
    "x",
]

OUT = Path(__file__).resolve().parent.parent / "src" / "icons" / "lucide"

def fetch(path: str) -> bytes:
    with urllib.request.urlopen(f"{BASE_URL}/{path}", timeout=30) as response:
        return response.read()

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    # First, download every icon we use, and stop if one of the names is wrong.
    for name in ICONS:
        try:
            svg = fetch(f"icons/{name}.svg")
        except OSError as e:
            sys.exit(f"Couldn't get the {name!r} icon ({e}). Check the name on lucide.dev.")
        OUT.joinpath(f"{name}.svg").write_bytes(svg)
        print(f"Got {name}")
    # Then remove icons we don't use anymore, so only the listed ones ship.
    for file in OUT.glob("*.svg"):
        if file.stem not in ICONS:
            file.unlink()
            print(f"Removed {file.stem}")
    # Finally, keep Lucide's license next to the icons.
    OUT.joinpath("LICENSE").write_bytes(fetch("LICENSE"))

if __name__ == "__main__":
    main()
