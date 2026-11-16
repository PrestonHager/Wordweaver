# test/__init__.py

from .test_wordweaver_project import TestProject

__all__ = ["TestProject"]

if __name__ == "__main__":
    import unittest
    unittest.main()
