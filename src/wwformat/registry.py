# wwformat/registry.py

from enum import IntEnum, unique

from google.protobuf.message import Message
from google.protobuf.message_factory import GetMessageClass

from wwformat import wordweaver_pb2 as pb
from wwformat.container import PATCH_TYPE_ID

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
    ALLOPHONE_RULES = 17
    # 19 is unused, and 23 is held for Phonotactic Constraints.
    SYLLABLE_STRUCTURES = 21
    # Patches sit at the top of the one-byte range so record tables can keep counting up from the bottom.
    # The container needs to know it too, to drop a cut-off patch.
    PATCH = PATCH_TYPE_ID

def is_critical(type_id: int) -> bool:
    return type_id % 2 == 1

# Chunks that hold a single message.
SINGLE_MESSAGES: dict[ChunkType, type[Message]] = {
    ChunkType.STRING_TABLE: pb.StringTable,
    ChunkType.PROJECT: pb.ProjectInfo,
}

# Chunks that hold a table of records, each with a stable `id`.
# To add a new record type, add its messages to the .proto, give it a chunk type above, and list it here.
# Patches find records by table and ID, so a new table gets patch saves without any extra work.
RECORD_TABLES = {
    ChunkType.LANGUAGES: pb.LanguageTable,
    ChunkType.PHONEMES: pb.PhonemeTable,
    ChunkType.ENTRIES: pb.EntryTable,
    ChunkType.DEFINITIONS: pb.DefinitionTable,
    ChunkType.TAGS: pb.TagTable,
    ChunkType.PHONEME_CLASSES: pb.PhonemeClassTable,
    ChunkType.ALLOPHONE_RULES: pb.AllophoneRuleTable,
    ChunkType.SYLLABLE_STRUCTURES: pb.SyllableStructureTable,
}

def record_class(table: ChunkType) -> type[Message]:
    """Get the record message for a table, like pb.Phoneme for PHONEMES."""
    return GetMessageClass(RECORD_TABLES[table].DESCRIPTOR.fields_by_name["records"].message_type)
