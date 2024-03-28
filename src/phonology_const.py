# phonology_const.py

PULMONIC_CONSONANTS = {
    "plosive": {
        "bi-labial": {
            "voiced": "p",
            "voiceless": "b"
        },
        "alveolar": {
            "voiced": "t"
        },
        "post-alveolar": {
            "voiced": "d"
        },
        "retroflex": {
            "voiced": "\u0288",
            "voiceless": "\u0256"
        },
        "palatal": {
            "voiced": "c",
            "voiceless": "\u025f"
        },
        "velar": {
            "voiced": "k",
            "voiceless": "g"
        },
        "uvular": {
            "voiced": "q",
            "voiceless": "\u0262"
        },
        "glottal": {
            "voiceless": "\u0294"
        }
    },
    "nasal": {
        "bi-labial": {
            "voiced": "m"
        },
        "labio-dental": {
            "voiced": "\u0271"
        },
        "post-alveolar": {
            "voiced": "n"
        },
        "retroflex": {
            "voiced": "\u0273"
        },
        "palatal": {
            "voiced": "\u0272"
        },
        "velar": {
            "voiced": "\u014b"
        },
        "uvular": {
            "voiced": "\u0274"
        }
    },
    "trill": {
        "bi-labial": {
            "voiced": "\u0299"
        },
        "post-alveolar": {
            "voiced": "r"
        },
        "uvular": {
            "voiced": "\u0280"
        }
    },
    "tap": {
        "labio-dental": {
            "voiced": "\u2c71"
        },
        "post-alveolar": {
            "voiced": "\u027e"
        },
        "retroflex": {
            "voiced": "\u027d"
        }
    },
    "fricative": {
        "bi-labial": {
            "voiced": "\u0278",
            "voiceless": "\u03b2"
        },
        "labio-dental": {
            "voiced": "f",
            "voiceless": "v"
        },
        "dental": {
            "voiced": "\u03b8",
            "voiceless": "\u00f0"
        },
        "alveolar": {
            "voiced": "s",
            "voiceless": "z"
        },
        "post-alveolar": {
            "voiced": "\u0283",
            "voiceless": "\u0292"
        },
        "retroflex": {
            "voiced": "\u0282",
            "voiceless": "\u0290"
        },
        "palatal": {
            "voiced": "\u00e7",
            "voiceless": "\u029d"
        },
        "velar": {
            "voiced": "x",
            "voiceless": "\u0263"
        },
        "uvular": {
            "voiced": "\u03c7",
            "voiceless": "\u0281"
        },
        "pharyngeal": {
            "voiced": "\u0127",
            "voiceless": "\u0295"
        },
        "glottal": {
            "voiced": "h",
            "voiceless": "\u0266"
        }
    },
    "lateral-fricative": {
        "dental": {
            "voiced": "\u026c"
        },
        "post-alveolar": {
            "voiced": "\u026e"
        }
    },
    "approximant": {
        "labio-dental": {
            "voiced": "\u028b"
        },
        "post-alveolar": {
            "voiced": "\u0279"
        },
        "retroflex": {
            "voiced": "\u027b"
        },
        "palatal": {
            "voiced": "j"
        },
        "velar": {
            "voiced": "\u0270"
        }
    },
    "lateral-approximant": {
        "post-alveolar": {
            "voiced": "l"
        },
        "retroflex": {
            "voiced": "\u026d"
        },
        "palatal": {
            "voiced": "\u028e"
        },
        "velar": {
            "voiced": "\u029f"
        }
    }
}

NON_PULMONIC_CONSONANTS = {
}

VOWELS = {
    "close": {
        "front": {
            "unrounded": "i",
            "rounded": "y"
        },
        "central": {
            "unrounded": "\u0268",
            "rounded": "\u0289"
        },
        "back": {
            "unrounded": "\u026f",
            "rounded": "u"
        }
    },
    "medial-close-mid": {
        "front": {
            "unrounded": "\u026a",
            "rounded": "\u028f"
        },
        "back": {
            "unrounded": "\u028a"
        }
    },
    "close-mid": {
        "front": {
            "unrounded": "e",
            "rounded": "\u00f8"
        },
        "central": {
            "unrounded": "\u0258",
            "rounded": "\u0275"
        },
        "back": {
            "unrounded": "\u0264",
            "rounded": "o"
        }
    },
    "mid": {
        "central": {
            "unrounded": "\u0259"
        }
    },
    "open-mid": {
        "front": {
            "unrounded": "\u025b",
            "rounded": "\u0153"
        },
        "central": {
            "unrounded": "\u025c",
            "rounded": "\u025e"
        },
        "back": {
            "unrounded": "\u028c",
            "rounded": "\u0254"
        }
    },
    "medial-open-mid": {
        "front": {
            "unrounded": "\u00e6"
        },
        "central": {
            "unrounded": "\u0250"
        }
    },
    "open": {
        "front": {
            "unrounded": "a",
            "rounded": "\u0276"
        },
        "back": {
            "unrounded": "\u0251",
            "rounded": "\u0252"
        }
    }
}

__all__ = [
    "PULMONIC_CONSONANTS",
    "NON_PULMONIC_CONSONANTS",
    "VOWELS",
]
