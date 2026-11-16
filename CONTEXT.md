# Wordweaver

A toolbox for building constructed languages (conlangs).
This glossary covers the words we use for the languages, their sounds, their words, and how they're written and how they change.

## Projects and languages

**Project**:
A collection of Languages and Scripts, such as one language family or a whole invented world.
_Avoid_: Workspace, file

**Language**:
One conlang inside a Project, with its own Phoneme Inventory, Lexicon, Grammar, and Orthographies.
_Avoid_: Conlang (fine in casual talk, but not as a model name), project

**Descent**:
The link from a parent Language to a daughter Language that evolved from it.
A Language can have any number of parents and daughters.
_Avoid_: Inheritance (as a Language-level link), child, fork

**Language Kind**:
A label the user picks to describe a Language: Proto-Language, Language, Dialect, or Creole.
It's only a description and doesn't change how the Language works.
_Avoid_: Language type, role

**Proto-Language**:
A Language Kind for a Language that others descend from, usually simpler, used as the starting point for Language Change.
_Avoid_: Root language, base language

**Dialect**:
A Language Kind for a regional variety of another Language whose words and grammar differ, not just its pronunciation.
It's usually linked to that Language by Descent with only a few Changes.
_Avoid_: Variant, accent (that's pronunciation only)

## Sounds

**Phoneme**:
A single distinctive sound of a Language, written as an IPA symbol.
_Avoid_: Sound, character, IPAChar

**Phoneme Inventory**:
The set of Phonemes a Language uses.
_Avoid_: Phonology (that's the whole sound system, not just the set)

**Phoneme Class**:
A named group of Phonemes, like consonants, vowels, or nasals.
Classes overlap, so one Phoneme can be in many.
IPA features give the default Classes, and the user can change them.
_Avoid_: Category, type, Phonemes enum

**Phoneme Frequency**:
An optional weight saying how common a Phoneme is in a Language.
Phonemes without one are treated as equally common.
_Avoid_: Probability, chance

**Allophone**:
One of the ways a Phoneme is actually pronounced, like the flapped /t/ in English "butter".
_Avoid_: Variant, alternate sound

**Allophone Rule**:
A rule saying which Allophone a Phoneme is pronounced as in a given context.
_Avoid_: Pronunciation rule

**Suprasegmental**:
A property of a syllable rather than a single Phoneme: **Stress**, **Tone**, or **Length**.
_Avoid_: Prosody (fine in casual talk), accent (we'll save that word for regional pronunciation)

**Phonotactics**:
All of a Language's rules about how its Phonemes can combine.
_Avoid_: Constraints (on its own), syllable rules

**Syllable Structure**:
The allowed shape of a syllable, like `(C)V(C)`, built from Onset, Nucleus, and Coda positions that each draw from a Phoneme Class.
_Avoid_: Syllable pattern, template, constraint

**Onset**, **Nucleus**, **Coda**:
The beginning, core, and end of a syllable.

**Phonotactic Constraint**:
A rule that bans or limits which Phonemes can appear where, such as "no /ŋ/ in an Onset" or "no stops in a word's last Coda".
A constraint can depend on where the syllable sits in the word.
_Avoid_: Phonemic constraint, restriction

## Words

**Lexicon**:
A Language's dictionary of Entries.
_Avoid_: Dictionary, word list

**Entry**:
One item in a Lexicon, with one Form and one or more Definitions.
An Entry can be a Root, an Affix, or a word built from Morphemes.
_Avoid_: Word (too vague), lexeme

**Form**:
How an Entry is said in the conlang, written in IPA.
_Avoid_: Spelling (that's what an Orthography produces), value

**Definition**:
One precise meaning of an Entry.
It can be described with one or more Glosses, technical linguistic terms, or a longer description.
_Avoid_: Meaning (fine in casual talk), sense, translation

**Gloss**:
A short word or phrase in the user's native language that helps describe a Definition.
_Avoid_: Translation, key

**Gloss Language**:
The Project-level setting for which natural language Glosses are written in, as a code like `en`.
It defaults to English and decides which open dictionary is searched for Concept References.
_Avoid_: Native language (fine in casual talk), locale

**Concept Reference**:
An optional link from a Definition to one exact sense in an open dictionary, such as an Open English WordNet synset or a Concepticon concept.
_Avoid_: Dictionary link, source

**Polysemy**:
When one Entry has several related Definitions, like one word meaning both "river" and "road".
_Avoid_: Multiple meanings

**Homophone**:
One of two or more separate Entries that share a Form but have unrelated Definitions.
They may or may not be spelled the same.
_Avoid_: Duplicate

**Etymon**:
An earlier Entry that an Entry came from.
Each Etymon is marked inherited (from a parent Language) or borrowed (from any other Language), and an Entry can have several.
_Avoid_: Source, origin, ancestor

**Coinage**:
An Entry with no Etymon, made up from scratch by the user or the Word Generator.
_Avoid_: New word, original

**Borrowing**:
An Entry one Language takes from another Language it doesn't descend from.
_Avoid_: Import, copy

**Loanword**:
A Borrowing that takes the source Entry's Form, adapted to the borrower's sounds.
_Avoid_: Loan, foreign word

**Calque**:
A Borrowing that takes the source Entry's meaning and structure, but builds it from the borrower's own Morphemes.
_Avoid_: Loan translation (fine as a plain-language label)

**Word Generator**:
The tool that invents new Forms that follow a Language's Phonotactics and Phoneme Frequencies, skipping Forms already in the Lexicon.
_Avoid_: Phoneme generator, randomizer

## Grammar

**Morpheme**:
The smallest piece of a Language that carries meaning, either a Root or an Affix.
_Avoid_: Part, piece

**Root**:
A Morpheme that carries the core meaning of a word.
_Avoid_: Stem (a Root plus some Affixes), base

**Affix**:
A Morpheme that attaches to a Root, like a prefix or suffix.
_Avoid_: Ending, marker

**Part of Speech**:
The grammatical role of an Entry, like noun or verb.
_Avoid_: Word class, word type

**Grammatical Category**:
A kind of distinction a Language marks, like tense, number, or case.
Each has a set of **Values**, like past, plural, or accusative.
_Avoid_: Feature, attribute

**Inflection**:
Making different forms of the same word to show Grammatical Category Values, like "dog" and "dogs".
Inflected forms are generated by the Grammar, not stored in the Lexicon.
_Avoid_: Conjugation, declension (fine as plain-language labels for verbs and nouns)

**Derivation**:
Making a new Entry from an existing one, like "kindness" from "kind".
_Avoid_: Word building

**Inflection Class**:
A group of Entries that inflect the same way, like the strong verbs of English (*sing, sang, sung*).
Each Inflection Class has its own Inflection rules.
_Avoid_: Category, conjugation group, declension group

**Tag**:
A free label the user puts on Entries, like "animals" or "sacred words", for anything the Grammar doesn't cover.
_Avoid_: Category, group, label

**Paradigm**:
The full table of a word's inflected forms.
_Avoid_: Conjugation table

**Irregular Form**:
A cell in an Entry's Paradigm that doesn't follow its Inflection rules, so it's stored on the Entry.
It either comes out of Recalculation, when Changes reshape an inflected form, or is filled in by hand.
_Avoid_: Exception (that's a hand edit on a Descent link), override

**Suppletion**:
An Irregular Form built from a different Root, like English "go" and "went".
_Avoid_: Replacement

**Word Order**:
The basic order of subject, verb, and object in a sentence, like SOV or SVO.

**Morphological Type**:
How a Language builds words: isolating, agglutinative, fusional, or polysynthetic.
_Avoid_: Language type

## Writing

**Script**:
A set of Graphemes and a writing direction, which any Language in the Project can write with.
_Avoid_: Alphabet (that's only one kind), font

**Grapheme**:
One written symbol in a Script.
_Avoid_: Letter, character, glyph

**Glyph**:
The drawn shape of a Grapheme.
_Avoid_: Grapheme, icon

**Freehand Glyph**:
A Glyph the user draws by hand, which the app fits to smooth curves.
It can be drawn as pen strokes with a width, or as closed shapes.
_Avoid_: Handwritten glyph, handwriting (that sounds like handwriting recognition), sketch

**Smoothness**:
How much small wobble in a Freehand Glyph gets ignored when it's fitted to curves.
_Avoid_: Tolerance, precision

**Component**:
A Grapheme used as part of a bigger Grapheme, like a jamo in a Hangul block or a radical in a Chinese character.
A **Semantic Component** hints at meaning, and a **Phonetic Component** hints at sound.
_Avoid_: Particle (that's a Part of Speech), radical, stroke

**Orthography**:
A Language's conventions for writing its Forms in a Script, including spelling, punctuation, capitalization, and word breaks.
A Language can have several, with one marked as primary.
_Avoid_: Writing system, spelling, romanization (that's just one Orthography)

**Writing System Type**:
A label on an Orthography saying how it uses its Script: alphabet, abjad, abugida, syllabary, logography, or featural.
_Avoid_: Script type

**Keyboard Layout**:
A mapping from physical keys to Graphemes, so the user can type a Script outside the app.

## Texts

**Text**:
A passage written in one Language, made of Sentences.
_Avoid_: Document, corpus

**Sentence**:
One sentence of a Text, stored as a sequence of Morphemes so it can be shown in any Orthography.
_Avoid_: Line, string

**Interlinear Gloss**:
The standard linguistics layout for a Sentence: the text, its Morpheme breakdown, a Gloss for each Morpheme, and a free translation.
_Avoid_: Breakdown, annotation

**Grammar Sketch**:
A readable write-up of a Language's sounds, Phonotactics, Grammar, and Orthographies, made for export.
_Avoid_: Reference grammar (that's a much bigger book), summary

## Change

**Language Change**:
Any change on a Descent link that turns a parent Language's features into a daughter's.
There are four kinds: Sound Change, Semantic Change, Grammatical Change, and Syntactic Change.
Each one is shown with its technical name and a plain description.
_Avoid_: Evolution, mutation

Changes on a Descent link run in order, and that order (the relative chronology) matters.

**Sound Change**:
A Language Change that alters Phonemes in Forms, like "/p/ becomes /f/ between vowels".
_Avoid_: Sound rule, transformation

**Intermediate Stage**:
A named point partway through a Descent link's Changes, like "Middle Proto-X", that shows what the Entries looked like at that point without being a full Language.
It has no Lexicon, Grammar, or Texts of its own.
_Avoid_: Checkpoint, snapshot, sub-language

**Promotion**:
Turning an Intermediate Stage into a full Language, which splits its Descent link in two at that point.
_Avoid_: Conversion, upgrade

**Scope**:
Which Entries a Language Change applies to.
It can filter by Part of Speech, Inflection Class, or Tag.
_Avoid_: Filter, target

**Regular Change**:
A Language Change whose Scope is every Entry that matches its conditions.
_Avoid_: Sound law (fine in casual talk), global change

**Sporadic Change**:
A Language Change whose Scope is a chosen set of Entries, like an irregular swap that only hit a few words.
_Avoid_: Irregular change, one-off

**Semantic Change**:
A Language Change that alters an Entry's Definitions, like a meaning getting broader.

**Grammatical Change**:
A Language Change that alters Morphemes or Grammar, like a full word turning into an Affix.

**Syntactic Change**:
A Language Change that alters sentence structure, like a shift in Word Order.

**Recalculation**:
Rebuilding a daughter Language's inherited Entries from its parents by running the Language Changes again.
It only happens when the user asks for it.
_Avoid_: Refresh, sync, regenerate

**Exception**:
A hand edit to an inherited Entry, attached at a point on a Descent link (an Intermediate Stage or the end), that's kept through Recalculation.
Changes after that point still apply to it.
_Avoid_: Override, irregular (that's a grammar term)

## Translation

**Translator**:
A separate tool that turns native-language text into Sentences in a Language, and Sentences back into native-language text.
It works by matching word senses to Definitions through their Concept References.
_Avoid_: Translation service, AI

**Lexical Gap**:
A native-language sense that has no matching Definition in a Language.
_Avoid_: Missing word, unknown word

## Reserved

These words are set aside for later, so don't use them for anything else.

**Accent**:
A regional way of pronouncing a Language, made of its own Allophone Rules.
