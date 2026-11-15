# phonology_const.py

# NOTE: These follow the official IPA chart (2020). The chart puts dental,
# alveolar and post-alveolar in one column for everything but fricatives,
# so those sounds live under "alveolar" here.
PULMONIC_CONSONANTS = {
    "plosive": {
        "bi-labial": {
            "voiceless": "p",
            "voiced": "b"
        },
        "alveolar": {
            "voiceless": "t",
            "voiced": "d"
        },
        "retroflex": {
            "voiceless": "ʈ",
            "voiced": "ɖ"
        },
        "palatal": {
            "voiceless": "c",
            "voiced": "ɟ"
        },
        "velar": {
            "voiceless": "k",
            "voiced": "g"
        },
        "uvular": {
            "voiceless": "q",
            "voiced": "ɢ"
        },
        "glottal": {
            "voiceless": "ʔ"
        }
    },
    "nasal": {
        "bi-labial": {
            "voiced": "m"
        },
        "labio-dental": {
            "voiced": "ɱ"
        },
        "alveolar": {
            "voiced": "n"
        },
        "retroflex": {
            "voiced": "ɳ"
        },
        "palatal": {
            "voiced": "ɲ"
        },
        "velar": {
            "voiced": "ŋ"
        },
        "uvular": {
            "voiced": "ɴ"
        }
    },
    "trill": {
        "bi-labial": {
            "voiced": "ʙ"
        },
        "alveolar": {
            "voiced": "r"
        },
        "uvular": {
            "voiced": "ʀ"
        }
    },
    "tap": {
        "labio-dental": {
            "voiced": "ⱱ"
        },
        "alveolar": {
            "voiced": "ɾ"
        },
        "retroflex": {
            "voiced": "ɽ"
        }
    },
    "fricative": {
        "bi-labial": {
            "voiceless": "ɸ",
            "voiced": "β"
        },
        "labio-dental": {
            "voiceless": "f",
            "voiced": "v"
        },
        "dental": {
            "voiceless": "θ",
            "voiced": "ð"
        },
        "alveolar": {
            "voiceless": "s",
            "voiced": "z"
        },
        "post-alveolar": {
            "voiceless": "ʃ",
            "voiced": "ʒ"
        },
        "retroflex": {
            "voiceless": "ʂ",
            "voiced": "ʐ"
        },
        "palatal": {
            "voiceless": "ç",
            "voiced": "ʝ"
        },
        "velar": {
            "voiceless": "x",
            "voiced": "ɣ"
        },
        "uvular": {
            "voiceless": "χ",
            "voiced": "ʁ"
        },
        "pharyngeal": {
            "voiceless": "ħ",
            "voiced": "ʕ"
        },
        "glottal": {
            "voiceless": "h",
            "voiced": "ɦ"
        }
    },
    "lateral-fricative": {
        "alveolar": {
            "voiceless": "ɬ",
            "voiced": "ɮ"
        }
    },
    "approximant": {
        "labio-dental": {
            "voiced": "ʋ"
        },
        "alveolar": {
            "voiced": "ɹ"
        },
        "retroflex": {
            "voiced": "ɻ"
        },
        "palatal": {
            "voiced": "j"
        },
        "velar": {
            "voiced": "ɰ"
        }
    },
    "lateral-approximant": {
        "alveolar": {
            "voiced": "l"
        },
        "retroflex": {
            "voiced": "ɭ"
        },
        "palatal": {
            "voiced": "ʎ"
        },
        "velar": {
            "voiced": "ʟ"
        }
    }
}

# NOTE: The chart only gives examples for ejectives, so these are the ones it
# lists (p', t', k', s').
NON_PULMONIC_CONSONANTS = {
    "click": {
        "bi-labial": {
            "voiceless": "ʘ"
        },
        "dental": {
            "voiceless": "ǀ"
        },
        "alveolar": {
            "voiceless": "ǃ"
        },
        "palato-alveolar": {
            "voiceless": "ǂ"
        }
    },
    "lateral-click": {
        "alveolar": {
            "voiceless": "ǁ"
        }
    },
    "implosive": {
        "bi-labial": {
            "voiced": "ɓ"
        },
        "alveolar": {
            "voiced": "ɗ"
        },
        "palatal": {
            "voiced": "ʄ"
        },
        "velar": {
            "voiced": "ɠ"
        },
        "uvular": {
            "voiced": "ʛ"
        }
    },
    "ejective": {
        "bi-labial": {
            "voiceless": "pʼ"
        },
        "alveolar": {
            "voiceless": "tʼ"
        },
        "velar": {
            "voiceless": "kʼ"
        }
    },
    "ejective-fricative": {
        "alveolar": {
            "voiceless": "sʼ"
        }
    }
}

VOWELS = {
    "close": {
        "front": {
            "unrounded": "i",
            "rounded": "y"
        },
        "central": {
            "unrounded": "ɨ",
            "rounded": "ʉ"
        },
        "back": {
            "unrounded": "ɯ",
            "rounded": "u"
        }
    },
    "near-close": {
        "front": {
            "unrounded": "ɪ",
            "rounded": "ʏ"
        },
        "back": {
            "rounded": "ʊ"
        }
    },
    "close-mid": {
        "front": {
            "unrounded": "e",
            "rounded": "ø"
        },
        "central": {
            "unrounded": "ɘ",
            "rounded": "ɵ"
        },
        "back": {
            "unrounded": "ɤ",
            "rounded": "o"
        }
    },
    "mid": {
        "central": {
            "unrounded": "ə"
        }
    },
    "open-mid": {
        "front": {
            "unrounded": "ɛ",
            "rounded": "œ"
        },
        "central": {
            "unrounded": "ɜ",
            "rounded": "ɞ"
        },
        "back": {
            "unrounded": "ʌ",
            "rounded": "ɔ"
        }
    },
    "near-open": {
        "front": {
            "unrounded": "æ"
        },
        "central": {
            "unrounded": "ɐ"
        }
    },
    "open": {
        "front": {
            "unrounded": "a",
            "rounded": "ɶ"
        },
        "back": {
            "unrounded": "ɑ",
            "rounded": "ɒ"
        }
    }
}

__all__ = [
    "PULMONIC_CONSONANTS",
    "NON_PULMONIC_CONSONANTS",
    "VOWELS",
]
