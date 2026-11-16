# Domain Diagram

How the terms in `CONTEXT.md` relate to each other.
It's split into four diagrams by area, because one big diagram is too much for Mermaid to lay out.
Class names are the glossary terms with the spaces removed.

Update this whenever `CONTEXT.md` changes.

## Projects and change

```mermaid
classDiagram
    direction LR
    Project "1" *-- "*" Language
    Project "1" *-- "*" Script
    Language "*" --> "1" LanguageKind : Proto-Language, Language, Dialect, Creole
    Language "1" --> "*" Descent : parent
    Descent "*" --> "1" Language : daughter
    Descent "1" *-- "*" LanguageChange : ordered
    Descent "1" *-- "*" IntermediateStage : between Changes
    SoundChange --|> LanguageChange
    SemanticChange --|> LanguageChange
    GrammaticalChange --|> LanguageChange
    SyntacticChange --|> LanguageChange
    LanguageChange "1" --> "1" Scope
    RegularChange ..> Scope : all matching Entries
    SporadicChange ..> Scope : chosen Entries
    Scope ..> Entry : picks
    Scope ..> PartOfSpeech : filters by
    Scope ..> InflectionClass : filters by
    Scope ..> Tag : filters by
    Promotion ..> IntermediateStage : turns into Language
    Recalculation ..> Descent : reruns Changes
    Recalculation ..> Entry : rebuilds inherited
    ChangeException ..> Entry : hand edit kept
    ChangeException ..> IntermediateStage : attached at
    class ChangeException["Exception"]
```

## Translation

```mermaid
classDiagram
    direction LR
    Translator ..> Sentence : produces and reads
    Translator ..> ConceptReference : matches senses by
    ConceptReference ..> Definition : points from
    Translator ..> LexicalGap : reports
    LexicalGap ..> WordGenerator : can be filled by
```

## Sounds

```mermaid
classDiagram
    direction LR
    Language "1" *-- "1" PhonemeInventory
    Language "1" *-- "1" Phonotactics
    PhonemeInventory "1" o-- "*" Phoneme
    PhonemeClass "*" o-- "*" Phoneme : groups
    Phoneme "1" --> "0..1" PhonemeFrequency
    Phoneme "1" --> "*" Allophone
    Phonotactics "1" *-- "*" SyllableStructure
    Phonotactics "1" *-- "*" PhonotacticConstraint
    Phonotactics "1" *-- "*" AllophoneRule
    AllophoneRule ..> Allophone : picks
    SyllableStructure ..> PhonemeClass : Onset, Nucleus, Coda
    SyllableStructure ..> Suprasegmental : Stress, Tone, Length
    PhonotacticConstraint ..> PhonemeClass : limits
    WordGenerator ..> Phonotactics : follows
    WordGenerator ..> PhonemeFrequency : weighs by
```

## Words and grammar

```mermaid
classDiagram
    direction LR
    Language "1" *-- "1" Lexicon
    Lexicon "1" *-- "*" Entry
    Entry "1" *-- "1" Form
    Entry "1" *-- "1..*" Definition
    Definition "1" o-- "*" Gloss
    Definition "1" --> "0..1" ConceptReference
    Project "1" --> "1" GlossLanguage
    Gloss ..> GlossLanguage : written in
    GlossLanguage ..> ConceptReference : picks the wordnet to search
    Entry "1" --> "*" Etymon : came from
    Etymon ..> Entry : earlier Entry
    Borrowing --|> Etymon
    Loanword --|> Borrowing
    Calque --|> Borrowing
    WordGenerator ..> Form : coins
    Entry ..> Morpheme : is or is built from
    Root --|> Morpheme
    Affix --|> Morpheme
    Entry "*" --> "0..1" PartOfSpeech
    Entry "*" --> "0..1" InflectionClass
    Entry "*" --> "*" Tag
    ConceptList ..> Lexicon : seeds unfinished Entries
    ConceptList ..> ConceptReference : links each seeded Entry
    InflectionClass "1" *-- "*" Inflection
    Language "1" *-- "*" GrammaticalCategory
    GrammaticalCategory "1" *-- "*" Value
    Inflection ..> Value : marks
    Inflection ..> Paradigm : fills
    Entry "1" *-- "*" IrregularForm : stored Paradigm cells
    IrregularForm ..> Paradigm : replaces a cell of
    Suppletion --|> IrregularForm
    Derivation ..> Entry : makes new
    Language "1" --> "1" WordOrder
    Language "1" --> "1" MorphologicalType
```

## Writing and texts

```mermaid
classDiagram
    direction LR
    Project "1" *-- "*" Script
    Script "1" *-- "*" Grapheme
    Grapheme "1" --> "0..1" Glyph
    FreehandGlyph --|> Glyph
    FreehandGlyph "1" --> "1" Smoothness
    Grapheme "1" *-- "*" Component
    Component ..> Grapheme : is a
    SemanticComponent --|> Component
    PhoneticComponent --|> Component
    Language "1" *-- "*" Orthography
    Orthography "*" --> "1" Script : writes with
    Orthography "1" --> "1" WritingSystemType
    Orthography ..> Form : spells
    KeyboardLayout ..> Script : types
    Language "1" *-- "*" Text
    Text "1" *-- "*" Sentence
    Sentence "1" o-- "*" Morpheme
    InterlinearGloss ..> Sentence : lays out
    GrammarSketch ..> Language : describes
```
