# test/test_phonotactics.py

import os
import tempfile
import unittest

# Add the parent directory to the path so we can import the module we want to test
import sys
from os import path
sys.path.append(path.abspath(path.join(path.dirname(__file__), '../src')))

from lexicon import Form
from phonotactics import CantSyllabify, ConstraintAtom, ConstraintMode, SyllablePart, SyllablePosition, write_syllables
from wordweaver_project import Project

class TestPhonotactics(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.file = path.join(self.temp_dir.name, "test.wwproj")
        self.project = Project("Test Project")
        self.language = self.project.add_language("Test")
        self.language.inventory.set_symbols(["p", "t", "k", "s", "m", "n", "l", "a", "i", "u"])
        self.phonotactics = self.language.phonotactics

    def tearDown(self):
        self.temp_dir.cleanup()

    def split(self, form: str) -> str | None:
        syllables = self.phonotactics.syllabify(form)
        return None if syllables is None else write_syllables(syllables)

    def passes(self, form: str) -> bool:
        return self.phonotactics.check(form) == []

    def round_trip(self):
        self.project.save(self.file)
        self.assertFalse(self.project.is_dirty)
        return Project.load(self.file).languages[0]

    def test_default_classes_have_labels(self):
        self.assertEqual(self.language.class_with_label("C").name, "Consonant")
        self.assertEqual(self.language.class_with_label("V").name, "Vowel")
        self.assertEqual(self.language.class_with_label("N").symbols, ["m", "n"])
        self.assertEqual(self.language.class_with_label("S").symbols, ["p", "t", "k"])
        self.assertIsNone(self.language.class_with_label("Q"))

    def test_any_class_can_get_a_label(self):
        liquids = self.language.add_class("Liquid", "R")
        liquids.add("l")
        self.assertIs(self.language.class_with_label("R"), liquids)
        sibilant = self.language.get_class("Sibilant")
        sibilant.label = "Z"
        self.assertIs(self.language.class_with_label("Z"), sibilant)
        # Labels are a capital letter, maybe with small letters or digits after it, and each one is used once.
        for bad in ("c", "CC", "C ", "(C)", "1", "V"):
            with self.assertRaises(ValueError):
                liquids.label = bad
        self.assertEqual(liquids.label, "R")
        liquids.label = "Lq2"
        liquids.label = ""
        self.assertEqual(liquids.label, "")
        with self.assertRaises(ValueError):
            self.language.add_class("Other", "C")

    def test_notation_is_tidied_and_split_into_parts(self):
        structure = self.phonotactics.add_syllable_structure(" (C) (C) V (C) ")
        self.assertEqual(structure.notation, "(C)(C)V(C)")
        self.assertEqual([(p.label, p.optional) for p in structure.positions], [("C", True), ("C", True), ("V", False), ("C", True)])
        self.assertEqual([p.part for p in structure.positions], [SyllablePart.ONSET, SyllablePart.ONSET, SyllablePart.NUCLEUS, SyllablePart.CODA])
        self.assertEqual(len(structure.part(SyllablePart.ONSET)), 2)
        self.assertEqual(structure.part(SyllablePart.NUCLEUS)[0].phoneme_class.name, "Vowel")
        self.assertEqual(self.phonotactics.syllable_structures, [structure])

    def test_bad_notation_is_refused(self):
        for bad in ("", "(C", "(CC)V", "C)V", "CvC", "QV", "CC", "(V)", "C?V"):
            with self.subTest(notation=bad), self.assertRaises(ValueError):
                self.phonotactics.add_syllable_structure(bad)
        self.phonotactics.add_syllable_structure("CV")
        with self.assertRaises(ValueError):
            self.phonotactics.add_syllable_structure("C V")
        self.assertEqual([s.notation for s in self.phonotactics.syllable_structures], ["CV"])

    def test_optional_positions_and_clusters(self):
        self.phonotactics.add_syllable_structure("(C)(C)V(C)")
        for form in ("a", "ta", "sta", "stat"):
            with self.subTest(form=form):
                self.assertTrue(self.passes(form))
        # Three consonants is one too many for the Onset, and two is one too many for the Coda.
        for form in ("psta", "stast", "st"):
            with self.subTest(form=form):
                self.assertFalse(self.passes(form))
        syllables = self.phonotactics.syllabify("stat")
        assert syllables is not None
        syllable = syllables[0]
        self.assertEqual((syllable.onset, syllable.nucleus, syllable.coda), (("s", "t"), ("a",), ("t",)))

    def test_positions_can_name_any_class(self):
        self.phonotactics.add_syllable_structure("(S)V(N)")
        self.assertTrue(self.passes("pan"))
        self.assertTrue(self.passes("am"))
        # /s/ isn't a stop, and /t/ isn't a nasal.
        self.assertFalse(self.passes("san"))
        self.assertFalse(self.passes("pat"))

    def test_syllabify_by_maximal_onset(self):
        self.phonotactics.add_syllable_structure("(C)(C)V(C)")
        self.assertEqual(self.split("asta"), "a.sta")
        self.assertEqual(self.split("tasta"), "ta.sta")
        # /nm/ is allowed as an Onset here, so it all goes to the second syllable.
        self.assertEqual(self.split("tanmi"), "ta.nmi")
        self.assertEqual(self.split("aia"), "a.i.a")
        # With only one Onset consonant allowed, the /s/ has to go in the Coda instead.
        only_one = self.phonotactics.syllable_structures[0]
        only_one.notation = "CV(C)"
        self.assertEqual(self.split("tasta"), "tas.ta")
        self.assertEqual(self.split("tanmi"), "tan.mi")

    def test_several_structures(self):
        self.phonotactics.add_syllable_structure("CV")
        self.phonotactics.add_syllable_structure("V(N)")
        self.assertEqual(self.split("anpa"), "an.pa")
        self.assertEqual(self.split("pama"), "pa.ma")
        self.assertFalse(self.passes("pat"))

    def test_form_that_cant_be_split(self):
        self.phonotactics.add_syllable_structure("CV")
        violations = self.phonotactics.check("pta")
        self.assertEqual(len(violations), 1)
        self.assertIsInstance(violations[0], CantSyllabify)
        self.assertIn("pta", violations[0].message)
        self.assertIsNone(self.phonotactics.syllabify("pta"))
        # A Phoneme that isn't in the inventory doesn't fit any Class either.
        self.assertIsInstance(self.phonotactics.check("ba")[0], CantSyllabify)

    def test_checking_forms_and_empty_forms(self):
        # Without any Syllable Structures, nothing can be split.
        self.assertIsInstance(self.phonotactics.check("pa")[0], CantSyllabify)
        self.phonotactics.add_syllable_structure("CV")
        self.assertTrue(self.passes("papa"))
        self.assertEqual(self.phonotactics.check(Form(["p", "a"])), [])
        # An unfinished Entry has an empty Form, and that passes.
        self.assertEqual(self.phonotactics.check(""), [])
        self.assertEqual(self.phonotactics.syllabify(Form()), [])

    def test_generate_forms_is_seeded_and_checks_constraints(self):
        self.phonotactics.add_syllable_structure("(C)V")
        first = self.project.generate_forms(self.language, 20, (1, 2), seed=42)
        second = self.project.generate_forms(self.language, 20, (1, 2), seed=42)
        self.assertEqual(first, second)
        self.assertEqual(len(first), 20)
        self.assertTrue(all(not self.phonotactics.check(form) for form in first))

    def test_generation_reports_impossible_rules(self):
        self.phonotactics.add_syllable_structure("V")
        self.phonotactics.add_constraint([ConstraintAtom("V", True)])
        with self.assertRaisesRegex(ValueError, "Couldn't generate"):
            self.project.generate_forms(self.language, 1, (1, 1), seed=1, attempt_limit=3)

    def test_generation_backtracks_around_banned_phoneme(self):
        self.phonotactics.add_syllable_structure("CV")
        self.phonotactics.add_constraint([ConstraintAtom("p", False)], SyllablePart.ONSET)
        forms = self.project.generate_forms(self.language, 1, (1, 1), seed=1, attempt_limit=1)
        self.assertNotEqual(forms[0], Form(["p", "a"]))
        self.assertFalse(self.phonotactics.check(forms[0]))

    def test_edit_and_remove_structures(self):
        structure = self.phonotactics.add_syllable_structure("CV")
        structure.notation = "CVC"
        self.assertEqual(structure.notation, "CVC")
        with self.assertRaises(ValueError):
            structure.notation = "CC"
        self.assertEqual(structure.notation, "CVC")
        self.assertFalse(self.passes("pa"))
        self.phonotactics.remove_syllable_structure(structure)
        self.assertEqual(self.phonotactics.syllable_structures, [])
        with self.assertRaises(ValueError):
            self.phonotactics.remove_syllable_structure(structure)

    def test_relabelled_class_leaves_a_problem(self):
        nasal = self.language.get_class("Nasal")
        structure = self.phonotactics.add_syllable_structure("CV(N)")
        self.phonotactics.add_syllable_structure("CV")
        self.assertIsNone(structure.problem)
        nasal.label = "M"
        # The structure stays as it was written, but it can't be used until something has the label again.
        self.assertEqual(structure.notation, "CV(N)")
        problem = structure.problem
        assert problem is not None
        self.assertIn("N", problem)
        self.assertFalse(self.passes("pan"))
        self.assertTrue(self.passes("pa"))
        nasal.label = "N"
        self.assertTrue(self.passes("pan"))

    def test_round_trip(self):
        liquids = self.language.add_class("Liquid", "R")
        liquids.add("l")
        first = self.phonotactics.add_syllable_structure("(C)(C)V(C)")
        second = self.phonotactics.add_syllable_structure("CV")
        self.phonotactics.remove_syllable_structure(second)
        third = self.phonotactics.add_syllable_structure("(S)V(R)")
        self.language.get_class("Sibilant").label = "Z"
        self.language.get_class("Fricative").label = ""
        loaded = self.round_trip()
        self.assertFalse(loaded.phonotactics.constraints)
        self.assertEqual([(s.id, s.notation) for s in loaded.phonotactics.syllable_structures], [(first.id, first.notation), (third.id, third.notation)])
        self.assertEqual(loaded.class_with_label("R").symbols, ["l"])
        self.assertEqual(loaded.class_with_label("Z").name, "Sibilant")
        self.assertEqual(loaded.get_class("Fricative").label, "")
        self.assertEqual(loaded.class_with_label("C").name, "Consonant")
        syllables = loaded.phonotactics.syllabify("pal")
        assert syllables is not None
        self.assertEqual(write_syllables(syllables), "pal")
        # New IDs after loading don't clash with the loaded structures.
        self.assertGreater(loaded.phonotactics.add_syllable_structure("V").id, third.id)

    def test_round_trip_through_patches(self):
        structure = self.phonotactics.add_syllable_structure("CV")
        gone = self.phonotactics.add_syllable_structure("V")
        # Pad the file out, so the patch stays under the size where saving compacts by itself.
        for _ in range(60):
            self.project.tags.add(os.urandom(16).hex())
        self.project.save(self.file)
        with open(self.file, "rb") as f_in:
            base = f_in.read()
        # Now edit one structure, remove another, add one, and relabel a Class, then save again as a patch.
        structure.notation = "(C)V(N)"
        self.phonotactics.remove_syllable_structure(gone)
        added = self.phonotactics.add_syllable_structure("(C)(C)V")
        self.language.get_class("Nasal").label = "Nm"
        self.project.save()
        with open(self.file, "rb") as f_in:
            self.assertTrue(f_in.read().startswith(base))
        loaded = Project.load(self.file).languages[0]
        self.assertEqual([(s.id, s.notation) for s in loaded.phonotactics.syllable_structures], [(structure.id, "(C)V(N)"), (added.id, "(C)(C)V")])
        self.assertEqual(loaded.class_with_label("Nm").name, "Nasal")
        self.assertIsNotNone(loaded.phonotactics.syllable_structures[0].problem)
        self.assertEqual(self.split("sta"), "sta")

    def test_constraints_ban_phonemes_classes_and_positions(self):
        self.phonotactics.add_syllable_structure("CVC")
        stop = self.language.get_class("Stop")
        assert stop is not None
        self.language.inventory.add("ŋ")
        constraint = self.phonotactics.add_constraint(
            [ConstraintAtom("ŋ", False)], SyllablePart.ONSET)
        self.assertTrue(self.passes("pat"))
        self.assertFalse(self.passes("ŋat"))
        self.phonotactics.remove_constraint(constraint)
        self.phonotactics.add_constraint([ConstraintAtom("Stop", True)], SyllablePart.CODA, SyllablePosition.LAST)
        self.assertFalse(self.passes("pat"))
        self.assertTrue(self.passes("pam"))

    def test_constraints_can_ban_sequences_across_syllable_boundaries(self):
        self.phonotactics.add_syllable_structure("(C)V(C)")
        stop = self.language.get_class("Stop")
        assert stop is not None
        stop.label = "Sx"
        self.phonotactics.add_constraint(
            [ConstraintAtom("Sx", True), ConstraintAtom("Sx", True)], across_boundaries=True)
        self.assertFalse(self.passes("patka"))
        self.assertTrue(self.passes("pasta"))

    def test_allow_constraints_can_shape_first_and_non_first_syllables(self):
        self.phonotactics.add_syllable_structure("V")
        self.phonotactics.add_syllable_structure("CV")
        self.phonotactics.add_constraint([ConstraintAtom("V", True)], position=SyllablePosition.FIRST,
                                          mode=ConstraintMode.ALLOW)
        self.phonotactics.add_constraint([ConstraintAtom("C", True), ConstraintAtom("V", True)],
                                          position=SyllablePosition.NON_FIRST, mode=ConstraintMode.ALLOW)
        self.assertTrue(self.passes("apapa"))
        self.assertFalse(self.passes("papa"))
        self.assertFalse(self.passes("apaia"))

    def test_constraints_round_trip(self):
        self.phonotactics.add_syllable_structure("V")
        self.phonotactics.add_constraint([ConstraintAtom("V", True)], position=SyllablePosition.FIRST,
                                          mode=ConstraintMode.ALLOW)
        self.project.save(self.file)
        loaded = Project.load(self.file).languages[0].phonotactics
        self.assertEqual(len(loaded.constraints), 1)
        self.assertEqual(loaded.constraints[0].mode, ConstraintMode.ALLOW)
        self.assertEqual(loaded.constraints[0].position, SyllablePosition.FIRST)

if __name__ == "__main__":
    unittest.main()
