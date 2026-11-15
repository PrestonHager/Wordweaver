# Irregular forms come from recalculating whole paradigms

Recalculation runs Language Changes on every cell of each inherited Entry's Paradigm, not just on its Morphemes.
When an evolved cell doesn't match what the daughter's own Inflection rules would make, it's stored on the Entry as an Irregular Form.
We did this so that irregular verbs and nouns come out of a Language's history the way they do in natural languages, like English "foot" and "feet".
You can still make Irregular Forms by hand, through Inflection Classes or Suppletion.

## Considered Options

- **Changes only run on Morphemes**: simpler and faster, but irregular forms could never come about on their own, only by hand.

## Consequences

- Recalculation is heavier, since it has to generate and evolve every Paradigm cell.
- Changing a daughter's Inflection rules can turn stored Irregular Forms back into regular ones, or the other way around.
