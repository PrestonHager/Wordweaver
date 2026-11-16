# test/test_search.py

import unittest

# Add the parent directory to the path so we can import the module we want to test
import sys
from os import path
sys.path.append(path.abspath(path.join(path.dirname(__file__), '../src')))

from lexicon import SearchField, SortOrder
from wordweaver_project import Project

class TestSearch(unittest.TestCase):
    def setUp(self):
        self.project = Project("Test Project")
        self.language = self.project.add_language("Test")
        self.lexicon = self.language.lexicon

    def glosses(self, entries) -> list[str]:
        # Each Entry's first Gloss is enough to tell them apart here.
        return [e.glosses[0] for e in entries]

    def test_search_by_form(self):
        self.lexicon.add("tasi", ["stone"])
        self.lexicon.add("ta", ["one"])
        self.lexicon.add("sita", ["bird"])
        self.lexicon.add("ŋi", ["eye"])
        # The exact Form comes first, then Forms starting with it, then Forms only containing it.
        self.assertEqual(self.glosses(self.lexicon.search("ta", SearchField.FORM)), ["one", "stone", "bird"])
        self.assertEqual(self.glosses(self.lexicon.search("ŋ i", SearchField.FORM)), ["eye"])
        self.assertEqual(self.lexicon.search("ku", SearchField.FORM), [])

    def test_form_search_keeps_case(self):
        # IPA letters that differ by case are different sounds, like /n/ and /N/.
        self.lexicon.add("Na", ["uvular"])
        self.lexicon.add("na", ["alveolar"])
        self.assertEqual(self.glosses(self.lexicon.search("na", SearchField.FORM)), ["alveolar"])

    def test_form_search_ignores_unicode_differences(self):
        # The same letter can be typed precomposed or with a combining mark.
        self.lexicon.add("tã", ["nasal"])
        self.assertEqual(self.glosses(self.lexicon.search("tã", SearchField.FORM)), ["nasal"])

    def test_empty_forms_never_match_a_form_search(self):
        self.lexicon.add("", ["water"])
        self.lexicon.add("a", ["and"])
        self.assertEqual(self.glosses(self.lexicon.search("a", SearchField.FORM)), ["and"])

    def test_search_by_gloss(self):
        self.lexicon.add("ka", ["waterfall"])
        self.lexicon.add("ti", ["salt water"])
        self.lexicon.add("su", ["drink", "Water"])
        self.lexicon.add("pa", ["fire"])
        # Case doesn't matter, and any Gloss of the Entry can match.
        self.assertEqual(self.glosses(self.lexicon.search("WATER", SearchField.GLOSS)), ["drink", "waterfall", "salt water"])

    def test_gloss_search_looks_at_every_definition(self):
        entry = self.lexicon.add("ta", ["river"])
        self.lexicon.add_definition(entry, ["road"])
        roadside = self.lexicon.add("ra", ["roadside"])
        self.assertEqual(self.lexicon.search("road", SearchField.GLOSS), [entry, roadside])

    def test_search_by_description(self):
        first = self.lexicon.add("ta", ["one"], description="The number one, used for counting.")
        second = self.lexicon.add("sa", ["two"])
        self.lexicon.add_definition(second, ["pair"], description="Counting things that come in twos.")
        self.lexicon.add("ni", ["three"], description="Counting")
        self.lexicon.add("ku", ["four"])
        self.assertEqual(self.glosses(self.lexicon.search("counting", SearchField.DESCRIPTION)), ["three", "two", "one"])
        self.assertEqual(self.lexicon.search("five", SearchField.DESCRIPTION), [])
        self.assertEqual(self.lexicon.search("number one", SearchField.DESCRIPTION), [first])

    def test_search_by_tag(self):
        animals = self.project.tags.add("animals")
        wolf = self.lexicon.add("ulka", ["wolf"])
        bear = self.lexicon.add("arka", ["bear"])
        self.lexicon.add("ka", ["wolfsbane"])
        self.lexicon.tag(wolf, animals)
        self.lexicon.tag(bear, animals)
        # A blank search lists everything with the Tag, and a text search only looks inside it.
        self.assertEqual(self.lexicon.search(tag=animals), [wolf, bear])
        self.assertEqual(self.lexicon.search("wolf", tag=animals), [wolf])

    def test_blank_search_lists_everything_in_lexicon_order(self):
        self.lexicon.add("ta", ["one"])
        self.lexicon.add("", ["two"])
        self.lexicon.add("ti", ["three"])
        for field in SearchField:
            self.assertEqual(self.glosses(self.lexicon.search("  ", field)), ["one", "two", "three"])

    def test_sort_by_form(self):
        self.lexicon.add("ti", ["one"])
        self.lexicon.add("", ["two"])
        self.lexicon.add("ka", ["three"])
        self.lexicon.add("ta", ["four"])
        # Empty Forms go last, since there's nothing to sort them by.
        self.assertEqual(self.glosses(self.lexicon.search(sort=SortOrder.FORM)), ["three", "four", "one", "two"])

    def test_sort_by_gloss(self):
        entry = self.lexicon.add("ti", ["water"])
        self.lexicon.add_definition(entry, ["apple"])
        self.lexicon.add("ka", ["Bird"])
        self.lexicon.add("ta", ["arm"])
        # Only the first Gloss of the first Definition counts, and case doesn't matter.
        self.assertEqual(self.glosses(self.lexicon.search(sort=SortOrder.GLOSS)), ["arm", "Bird", "water"])

    def test_sort_applies_to_search_results(self):
        self.lexicon.add("sa", ["water"])
        self.lexicon.add("ka", ["waterfall"])
        self.lexicon.add("ta", ["fire"])
        self.assertEqual(self.glosses(self.lexicon.search("water", sort=SortOrder.FORM)), ["waterfall", "water"])

if __name__ == '__main__':
    unittest.main()
