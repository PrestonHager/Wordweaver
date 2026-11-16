# test/test_compression.py

import json
import unittest
import tempfile

# Add the parent directory to the path so we can import the module we want to test
import sys
from os import path
sys.path.append(path.abspath(path.join(path.dirname(__file__), '../src')))

from ipapy import UNICODE_TO_IPA

from phonology import is_valid_phoneme
from wordweaver_project import Project

def as_dict(project: Project) -> dict:
    # The same data a user sees, written out the way a JSON project file would hold it.
    return {
        "name": project.name,
        "languages": [
            {
                "id": language.id,
                "name": language.name,
                "phonemes": [{"id": p.id, "symbol": p.symbol} for p in language.inventory],
                "classes": [{"id": c.id, "name": c.name, "symbols": c.symbols} for c in language.classes],
                "entries": [{"id": e.id, "form": str(e.form), "glosses": e.glosses} for e in language.lexicon],
            }
            for language in project.languages
        ],
    }

class TestCompression(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.file = path.join(self.temp_dir.name, "test.wwproj")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_smaller_than_json(self):
        symbols = [s for s in UNICODE_TO_IPA if is_valid_phoneme(s)][:60]
        project = Project("Big Project")
        for i in range(6):
            language = project.add_language(f"Language {i}")
            language.inventory.set_symbols(symbols)
            for j in range(30):
                phoneme_class = language.add_class(f"Class {j}")
                for symbol in symbols[j:j + 10]:
                    phoneme_class.add(symbol)
        project.save(self.file)
        self.assertGreater(sum(len(language.inventory) for language in project.languages), 300)
        self.assertEqual(as_dict(Project.load(self.file)), as_dict(project))
        self.assertLess(path.getsize(self.file), len(json.dumps(as_dict(project), ensure_ascii=False).encode()))

    def test_large_chunks_are_compressed(self):
        project = Project("Wordy Project")
        lexicon = project.add_language("Test").lexicon
        glosses = [f"the colour of the evening sky over the hills, kind {i}" for i in range(500)]
        for gloss in glosses:
            lexicon.add("", [gloss])
        project.save(self.file)
        # Every gloss is a different string, so only compression gets the file well under their total size.
        self.assertLess(path.getsize(self.file), sum(len(gloss) for gloss in glosses) / 3)
        self.assertEqual(as_dict(Project.load(self.file)), as_dict(project))

    def test_compressed_patches(self):
        project = Project("Wordy Project")
        lexicon = project.add_language("Test").lexicon
        project.save(self.file)
        size = path.getsize(self.file)
        glosses = [f"the colour of the evening sky over the hills, kind {i}" for i in range(500)]
        for gloss in glosses:
            lexicon.add("", [gloss])
        project.save()
        self.assertLess(path.getsize(self.file) - size, sum(len(gloss) for gloss in glosses) / 3)
        self.assertEqual(as_dict(Project.load(self.file)), as_dict(project))

if __name__ == "__main__":
    unittest.main()
