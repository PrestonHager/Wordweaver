# wwformat/container.py

# The low-level v1 container from ADR 0003:
#   header: magic (4 bytes, big-endian) | major (varint) | minor (varint)
#   chunk:  type ID (varint) | length (varint) | compression (1 byte) | payload | CRC32 (4 bytes, big-endian)
# The length covers the compression byte and payload, and the CRC covers everything before it.
# This layer only knows about bytes, not what's inside the payloads.

import zlib
from dataclasses import dataclass

from wwformat.errors import CorruptFileError, NewerVersionError, ProjectFileError

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

# How a chunk's payload is stored, from the byte in front of it.
RAW = 0
ZLIB = 1

# Payloads smaller than this aren't worth compressing, since zlib's own header would eat most of the savings.
COMPRESS_OVER = 256

def encode_chunk(chunk: Chunk) -> bytes:
    framed = bytes([RAW]) + chunk.payload
    # Compress big payloads, but only keep the result if it actually came out smaller.
    if len(chunk.payload) > COMPRESS_OVER:
        compressed = bytes([ZLIB]) + zlib.compress(chunk.payload, 9)
        if len(compressed) < len(framed):
            framed = compressed
    body = encode_varint(chunk.type_id) + encode_varint(len(framed)) + framed
    return body + zlib.crc32(body).to_bytes(4, "big")

def encode_file(chunks: list[Chunk], major: int=MAJOR_VERSION, minor: int=MINOR_VERSION) -> bytes:
    header = MAGIC.to_bytes(4, "big") + encode_varint(major) + encode_varint(minor)
    return header + b"".join(encode_chunk(chunk) for chunk in chunks)

# Patch chunks are the only ones a crash can cut off, since they're appended to a finished file.
# ChunkType.PATCH uses this.
# NOTE: keep it under 128, so a cut-off patch always has its whole one-byte type ID to go on.
PATCH_TYPE_ID = 127

@dataclass
class DecodedFile:
    major: int
    minor: int
    chunks: list[Chunk]
    # True when a broken patch at the end of the file was dropped.
    dropped_patch: bool = False
    # How many bytes of the file are patch chunks.
    patch_bytes: int = 0

def decode_file(data: bytes) -> DecodedFile:
    """Split file bytes into chunks, checking every chunk's CRC."""
    # First, check that this is a Wordweaver file at all.
    if len(data) < 4 or int.from_bytes(data[:4], "big") != MAGIC:
        raise ProjectFileError("This isn't a Wordweaver Project file")
    major, pos = decode_varint(data, 4)
    minor, pos = decode_varint(data, pos)
    decoded = DecodedFile(major, minor, [])
    # Then read chunks until the end of the file.
    # The version and unknown chunk rules are checked one layer up, in FileContents.decode.
    while pos < len(data):
        start = pos
        type_id, pos = decode_varint(data, pos)
        try:
            chunk, pos = _decode_chunk_body(data, pos, type_id)
        except CorruptFileError:
            # If the last save was cut off or garbled, drop that patch and load the file as it was before it.
            if type_id == PATCH_TYPE_ID and _runs_to_end(data, pos):
                decoded.dropped_patch = True
                break
            raise
        decoded.chunks.append(chunk)
        if type_id == PATCH_TYPE_ID:
            decoded.patch_bytes += pos - start
    return decoded

def _decode_chunk_body(data: bytes, pos: int, type_id: int) -> tuple[Chunk, int]:
    # The type ID was already read, so `pos` is at the length. The CRC covers the type ID too.
    start = pos - len(encode_varint(type_id))
    length, pos = decode_varint(data, pos)
    end = pos + length
    if end + 4 > len(data):
        raise CorruptFileError("The file ends in the middle of a chunk")
    crc = int.from_bytes(data[end:end + 4], "big")
    if zlib.crc32(data[start:end]) != crc:
        raise CorruptFileError(f"This Project file is damaged (chunk {type_id} failed its CRC check)")
    if length == 0:
        raise CorruptFileError(f"This Project file is damaged (chunk {type_id} is missing its compression byte)")
    return Chunk(type_id, _unframe(type_id, data[pos], data[pos + 1:end])), end + 4

def _unframe(type_id: int, compression: int, payload: bytes) -> bytes:
    if compression == RAW:
        return payload
    if compression == ZLIB:
        try:
            return zlib.decompress(payload)
        except zlib.error as e:
            raise CorruptFileError(f"This Project file is damaged (chunk {type_id} couldn't be decompressed)") from e
    raise NewerVersionError(f"This Project was saved by a newer version of Wordweaver (chunk {type_id} uses compression {compression}). Update Wordweaver to open it.")

def _runs_to_end(data: bytes, pos: int) -> bool:
    # Check that a broken chunk is the last thing in the file, so we never drop a patch with others after it.
    try:
        length, pos = decode_varint(data, pos)
    except CorruptFileError:
        return True
    return pos + length + 4 >= len(data)
