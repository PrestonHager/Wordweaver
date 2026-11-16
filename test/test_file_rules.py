# test/test_file_rules.py
#
# These build .wwproj bytes by hand, so they don't lean on the code that writes files.

import unittest
import tempfile
import zlib

# Add the parent directory to the path so we can import the module we want to test
import sys
from os import path
sys.path.append(path.abspath(path.join(path.dirname(__file__), '../src')))

from wordweaver_project import Project, CorruptFileError, NewerVersionError, ProjectFileError, UnknownChunkError

MAGIC = (0x87AFFA87).to_bytes(4, "big")
STRING_TABLE = 1
PROJECT = 3

def varint(value: int) -> bytes:
    out = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            out.append(byte | 0x80)
        else:
            out.append(byte)
            return bytes(out)

RAW = 0
ZLIB = 1

def chunk(type_id: int, payload: bytes=b"", compression: int=RAW) -> bytes:
    # Each payload starts with a byte saying how the rest of it is compressed.
    framed = bytes([compression]) + (zlib.compress(payload) if compression == ZLIB else payload)
    body = varint(type_id) + varint(len(framed)) + framed
    return body + zlib.crc32(body).to_bytes(4, "big")

def project_file(*extra_chunks: bytes, major: int=1, minor: int=0) -> bytes:
    # An empty string table and Project info is the smallest file that loads.
    return MAGIC + varint(major) + varint(minor) + chunk(STRING_TABLE) + chunk(PROJECT) + b"".join(extra_chunks)

class TestFileRules(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.file = path.join(self.temp_dir.name, "test.wwproj")

    def tearDown(self):
        self.temp_dir.cleanup()

    def load(self, data: bytes) -> Project:
        with open(self.file, "wb") as f_out:
            f_out.write(data)
        return Project.load(self.file)

    def test_smallest_file_loads(self):
        project = self.load(project_file())
        self.assertEqual(project.name, "")
        self.assertEqual(project.languages, [])

    def test_newer_major_version_is_refused(self):
        with self.assertRaises(NewerVersionError) as caught:
            self.load(project_file(major=2))
        self.assertIn("update", str(caught.exception).lower())

    def test_newer_minor_version_opens(self):
        project = self.load(project_file(minor=7))
        self.assertEqual(project.name, "")

    def test_unknown_critical_chunk_is_refused(self):
        with self.assertRaises(UnknownChunkError) as caught:
            self.load(project_file(chunk(1001, b"something new")))
        self.assertIn("1001", str(caught.exception))

    def test_unknown_ancillary_chunk_is_kept(self):
        extra = chunk(1000, b"from a newer app")
        project = self.load(project_file(extra))
        project.add_language("Added")
        project.save()
        with open(self.file, "rb") as f_in:
            self.assertIn(extra, f_in.read())
        self.assertEqual(Project.load(self.file).languages[0].name, "Added")

    def test_unknown_ancillary_chunk_survives_compaction(self):
        extra = chunk(1000, b"from a newer app")
        project = self.load(project_file(extra))
        language = project.add_language("Added")
        for symbol in ["p", "t", "a"]:
            language.inventory.add(symbol)
            project.save()
        project.compact()
        with open(self.file, "rb") as f_in:
            self.assertIn(extra, f_in.read())
        self.assertEqual(Project.load(self.file).languages[0].inventory.symbols, ["p", "t", "a"])

    def test_compressed_chunk_loads(self):
        # A string table with the name "Squashed" at index 1, and Project info pointing at it.
        strings = b"\x0a\x08Squashed"
        info = b"\x08\x01"
        data = MAGIC + varint(1) + varint(0) + chunk(STRING_TABLE, strings, ZLIB) + chunk(PROJECT, info, ZLIB)
        self.assertEqual(self.load(data).name, "Squashed")

    def test_unknown_compression_is_refused(self):
        with self.assertRaises(NewerVersionError) as caught:
            self.load(project_file(chunk(1000, b"something", compression=9)))
        self.assertIn("update", str(caught.exception).lower())

    def test_bad_crc_on_base_chunk_is_corrupt(self):
        data = bytearray(project_file())
        # The string table chunk starts right after the 6 header bytes, and its CRC comes after its type, length, and flag byte.
        data[9] ^= 0xFF
        with self.assertRaises(CorruptFileError):
            self.load(bytes(data))

    def test_unsupported_old_version_is_refused(self):
        with self.assertRaises(ProjectFileError) as caught:
            self.load(project_file(major=0))
        self.assertNotIsInstance(caught.exception, NewerVersionError)

if __name__ == "__main__":
    unittest.main()
