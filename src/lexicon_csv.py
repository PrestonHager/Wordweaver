# lexicon_csv.py

"""Export a Lexicon to CSV, with one row per Definition.

Cells with several values (Glosses, technical terms, and Tags) are joined with "; ".
A Concept Reference is written as `source:id`, like `oewn:oewn-09213565-n`.
Inside a value, a backslash is written as "\\\\" and a semicolon as "\\;", so any value round-trips through split_values.
"""

import csv
import io
from collections.abc import Iterable

from lexicon import Definition, Lexicon
from tags import Tags

BOM = "﻿"
SEPARATOR = "; "
HEADER = ("Entry ID", "Form", "Definition", "Glosses", "Technical Terms", "Description", "Concept Reference", "Tags")

def export_csv(lexicon: Lexicon, tags: Tags | None=None) -> str:
    """Return the CSV text for a Lexicon, starting with a UTF-8 byte order mark.

    Write it to a file with newline="" and encoding="utf-8", so the line endings and the byte order mark stay as they are.

    :param tags: Tags | None: The Project's Tags, to look up Tag names. Defaults to the Lexicon's own.
    """
    tags = lexicon.tags if tags is None else tags
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(HEADER)
    for entry in lexicon:
        tag_names = [tags.get(tag_id).name for tag_id in entry.tag_ids] if tags is not None else []
        for number, definition in enumerate(entry.definitions, start=1):
            writer.writerow((
                entry.id,
                str(entry.form),
                number,
                join_values(definition.glosses),
                join_values(definition.terms),
                definition.description,
                _concept_reference(definition),
                join_values(tag_names),
            ))
    return BOM + out.getvalue()

def join_values(values: Iterable[str]) -> str:
    """Join several values into one cell, escaping backslashes and semicolons."""
    return SEPARATOR.join(value.replace("\\", "\\\\").replace(";", "\\;") for value in values)

def split_values(cell: str) -> list[str]:
    """Split a cell made by join_values back into its values. An empty cell has none."""
    if not cell:
        return []
    values = []
    value = []
    i = 0
    while i < len(cell):
        char = cell[i]
        if char == "\\" and i + 1 < len(cell):
            # An escaped character is kept as is, even if it's a semicolon.
            value.append(cell[i + 1])
            i += 2
            continue
        if char == ";":
            # Now we've hit a separator, so finish this value and skip the space after it.
            values.append("".join(value))
            value = []
            i += 2 if cell.startswith(SEPARATOR, i) else 1
            continue
        value.append(char)
        i += 1
    values.append("".join(value))
    return values

def _concept_reference(definition: Definition) -> str:
    # Write the reference as source:id, like oewn:oewn-09213565-n, so ConceptReference.parse can read it back.
    reference = definition.concept_reference
    return "" if reference is None else str(reference)

__all__ = ["BOM", "HEADER", "SEPARATOR", "export_csv", "join_values", "split_values"]
