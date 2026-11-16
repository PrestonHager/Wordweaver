# scripts/make_concept_list.py
#
# Build a concept list file in src/concept_lists from a Concepticon release.
# Run it from the repo root, like `uv run python scripts/make_concept_list.py Swadesh-1955-100 "Swadesh 100 (1955)" "A compact basic vocabulary list."`.
# It needs an internet connection, since it downloads the list and the concept table from GitHub.

import csv
import io
import json
import sys
import urllib.request
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "src"
sys.path.append(str(SRC))

from concepticon import CONCEPTICON_URL, CONCEPTICON_VERSION, LISTS_DIR

LIST_URL = "https://raw.githubusercontent.com/concepticon/concepticon-data/{version}/concepticondata/conceptlists/{list_id}.tsv"
SOURCE_URL = "https://github.com/concepticon/concepticon-data/blob/{version}/concepticondata/conceptlists/{list_id}.tsv"
ATTRIBUTION = ("List, Johann Mattis & Tjuka, Annika & Blum, Frederic & Kučerová, Alžběta & Ugarte, Carlos Barrientos & "
               "Rzymski, Christoph & Greenhill, Simon & Forkel, Robert (eds.) 2025. Concepticon v3.4.0. "
               "A Resource for the Linking of Concept Lists. Leipzig: Max Planck Institute for Evolutionary Anthropology. "
               "https://concepticon.clld.org")

def read_tsv(url: str) -> list[dict[str, str]]:
    with urllib.request.urlopen(url, timeout=60) as response:
        text = response.read().decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(text, newline=""), delimiter="\t", quoting=csv.QUOTE_NONE))

def main():
    if len(sys.argv) not in (3, 4):
        sys.exit("Usage: make_concept_list.py <Concepticon list ID> <name to show> [short description]")
    list_id, name = sys.argv[1:3]
    description = sys.argv[3] if len(sys.argv) == 4 else ""
    # First, grab the concept table for the definitions, then the list itself.
    definitions = {row["ID"]: row["DEFINITION"] for row in read_tsv(CONCEPTICON_URL)}
    rows = read_tsv(LIST_URL.format(version=CONCEPTICON_VERSION, list_id=list_id))
    concepts = []
    for row in rows:
        # Some lists have concepts Concepticon couldn't map, and those can't be linked, so we skip them.
        if not row.get("CONCEPTICON_ID"):
            continue
        concepts.append({
            "number": row["NUMBER"],
            "id": row["CONCEPTICON_ID"],
            "gloss": row["CONCEPTICON_GLOSS"],
            # Swadesh marks some words with a *, which isn't part of the word.
            "english": row.get("ENGLISH", "").strip().lstrip("*"),
            "definition": definitions.get(row["CONCEPTICON_ID"], ""),
        })
    header = {
        "id": list_id,
        "name": name,
        "description": description,
        "source": SOURCE_URL.format(version=CONCEPTICON_VERSION, list_id=list_id),
        "version": f"Concepticon {CONCEPTICON_VERSION}",
        "license": "CC-BY-4.0",
        "license_url": "https://creativecommons.org/licenses/by/4.0/",
        "attribution": ATTRIBUTION,
    }
    # Now write it with one concept per line, so the file stays small and diffs stay readable.
    lines = [json.dumps(header, ensure_ascii=False, indent=2)[:-2] + ",", '  "concepts": [']
    lines += ["    " + json.dumps(concept, ensure_ascii=False) + "," for concept in concepts]
    lines[-1] = lines[-1].rstrip(",")
    lines += ["  ]", "}", ""]
    out = LISTS_DIR / f"{list_id}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(f"Wrote {len(concepts)} concepts to {out}")

if __name__ == "__main__":
    main()
