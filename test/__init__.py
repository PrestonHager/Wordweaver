# test/__init__.py

from .test_phonology import TestPhonemeGenerator
from .test_wordweaver_project import TestWordweaverProject

__all__ = [
    "TestPhonemeGenerator",
    "TestWordweaverProject",
]

if __name__ == "__main__":
    import unittest
    unittest.main()
