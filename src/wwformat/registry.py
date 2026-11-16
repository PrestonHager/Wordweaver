# wwformat/registry.py

from enum import IntEnum, unique

from wwformat import wordweaver_pb2 as pb

# Every chunk type ID lives here, so nobody reuses one by accident.
# Odd IDs are critical (a reader must understand them), even IDs are ancillary (safe to skip).
# NOTE: never change or reuse an ID once it has shipped, only add new ones.
@unique
class ChunkType(IntEnum):
    STRING_TABLE = 1
    PROJECT = 3
    LANGUAGES = 5
    PHONEMES = 7
    ENTRIES = 9
    DEFINITIONS = 11
    TAGS = 13
    PHONEME_CLASSES = 15

def is_critical(type_id: int) -> bool:
    return type_id % 2 == 1

# Chunks that hold a single message.
SINGLE_MESSAGES = {
    ChunkType.STRING_TABLE: pb.StringTable,
    ChunkType.PROJECT: pb.ProjectInfo,
}

# Chunks that hold a table of records, each with a stable `id`.
# To add a new record type, add its messages to the .proto, give it a chunk type above, and list it here.
RECORD_TABLES = {
    ChunkType.LANGUAGES: pb.LanguageTable,
    ChunkType.PHONEMES: pb.PhonemeTable,
    ChunkType.ENTRIES: pb.EntryTable,
    ChunkType.DEFINITIONS: pb.DefinitionTable,
    ChunkType.TAGS: pb.TagTable,
    ChunkType.PHONEME_CLASSES: pb.PhonemeClassTable,
}
