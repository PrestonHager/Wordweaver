# wwformat/migrations.py

from collections.abc import Callable

from wwformat.container import Chunk, MAJOR_VERSION

# Migrations keyed by the major version they upgrade from.
# MIGRATIONS[1] would take the chunks of a v1 file and return them as v2 chunks.
# It's empty because v1 is the first version of the format.
MIGRATIONS: dict[int, Callable[[list[Chunk]], list[Chunk]]] = {}

def migrate(major: int, chunks: list[Chunk]) -> list[Chunk]:
    """Bring chunks from an older major version up to the current one, one version at a time."""
    while major < MAJOR_VERSION:
        chunks = MIGRATIONS[major](chunks)
        major += 1
    return chunks
