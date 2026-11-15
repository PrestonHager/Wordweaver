# wwformat/container.py

# The low-level v1 container from ADR 0003:
#   header: magic (4 bytes, big-endian) | major (varint) | minor (varint)
#   chunk:  type ID (varint) | length (varint) | payload | CRC32 (4 bytes, big-endian)
# The CRC covers the type ID, length, and payload.
# This layer only knows about bytes, not what's inside the payloads.

import zlib
from dataclasses import dataclass

from wwformat.errors import CorruptFileError, ProjectFileError

MAGIC = 0x87AFFA87
MAJOR_VERSION = 1
MINOR_VERSION = 0

@dataclass(frozen=True)
class Chunk:
    type_id: int
    payload: bytes

def encode_varint(value: int) -> bytes:
    if value < 0:
        raise ValueError("Varints can't be negative")
    # Write 7 bits at a time, low bits first, with the high bit set when more bytes follow.
    out = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            out.append(byte | 0x80)
        else:
            out.append(byte)
            return bytes(out)

def decode_varint(data: bytes, pos: int) -> tuple[int, int]:
    """Read a varint at `pos` and return it with the position just after it."""
    value = 0
    shift = 0
    while True:
        if pos >= len(data):
            raise CorruptFileError("The file ends in the middle of a number")
        byte = data[pos]
        pos += 1
        value |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return value, pos
        shift += 7

def encode_chunk(chunk: Chunk) -> bytes:
    body = encode_varint(chunk.type_id) + encode_varint(len(chunk.payload)) + chunk.payload
    return body + zlib.crc32(body).to_bytes(4, "big")

def encode_file(chunks: list[Chunk], major: int=MAJOR_VERSION, minor: int=MINOR_VERSION) -> bytes:
    header = MAGIC.to_bytes(4, "big") + encode_varint(major) + encode_varint(minor)
    return header + b"".join(encode_chunk(chunk) for chunk in chunks)

def decode_file(data: bytes) -> tuple[int, int, list[Chunk]]:
    """Split file bytes into (major, minor, chunks), checking every chunk's CRC."""
    # First, check that this is a Wordweaver file at all.
    if len(data) < 4 or int.from_bytes(data[:4], "big") != MAGIC:
        raise ProjectFileError("This isn't a Wordweaver Project file")
    major, pos = decode_varint(data, 4)
    minor, pos = decode_varint(data, pos)
    # Then read chunks until the end of the file.
    # TODO: the version and unknown chunk rules come in #31, and dropping a cut-off patch in #32.
    chunks = []
    while pos < len(data):
        start = pos
        type_id, pos = decode_varint(data, pos)
        length, pos = decode_varint(data, pos)
        end = pos + length
        if end + 4 > len(data):
            raise CorruptFileError("The file ends in the middle of a chunk")
        crc = int.from_bytes(data[end:end + 4], "big")
        if zlib.crc32(data[start:end]) != crc:
            raise CorruptFileError(f"Chunk {type_id} failed its CRC check")
        chunks.append(Chunk(type_id, data[pos:end]))
        pos = end + 4
    return major, minor, chunks
