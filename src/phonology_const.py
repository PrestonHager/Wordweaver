# phonology_const.py

PULMONIC_CONSONANTS = {
    "plosive": {
        "bi-labial": {
            "p": "p",
            "b": "b"
        },
        "alveolar": {
            "t": "t"
        },
        "post-alveolar": {
            "d": "d"
        },
        "retroflex": {
            "tr": "ʈ",
            "dr": "ɖ"
        },
        "palatal": {
            "c": "c",
            "cr": "ɟ"
        },
        "velar": {
            "k": "k",
            "g": "g"
        },
        "uvular": {
            "kv": "q",
            "gv": "ɢ"
        }, 
        "glottal": {
            "gh": "ʔ"
        }
    },
    "nasal": {
        "bi-labial": {
            "m": "m"
        },
        "labio-dental": {
            "mn": "ɱ"
        },
        "post-alveolar": {
            "n": "n"
        },
        "retroflex": {
            "ng1": "ɳ"
        },
        "palatal": {
            "ng2": "ɲ"
        },
        "velar": {
            "ng": "ŋ"
        },
        "uvular": {
            "nh": "ɴ"
        }
    },
    "trill": {
        "bi-labial": {
            "br": "ʙ"
        },
        "post-alveolar": {
            "r": "r"
        },
        "uvular": {
            "rr": "ʀ"
        }
    },
    "tap": {
        "labio-dental": {
            "vt": "ⱱ"
        },
        "post-alveolar": {
            "rt": "ɾ"
        },
        "retroflex": {
            "rf": "ɽ"
        }
    },
    "fricative": {
        "bi-labial": {
            "ph": "ɸ",
            "phv": "β"
        },
        "labio-dental": {
            "f": "f",
            "v": "v"
        },
        "dental": {
            "th": "θ",
            "thv": "ð"
        },
        "alveolar": {
            "s": "s",
            "z": "z"
        },
        "post-alveolar": {
            "sh": "ʃ",
            "zh": "ʒ"
        },
        "retroflex": {
            "sr": "ʂ",
            "zr": "ʐ"
        },
        "palatal": {
            "cx": "ç",
            "jx": "ʝ"
        },
        "velar": {
            "x": "x",
            "xz": "ɣ"
        },
        "uvular": {
            "fx": "χ",
            "fr": "ʁ"
        },
        "pharyngeal": {
            "fh": "ħ",
            "fg": "ʕ"
        },
        "glottal": {
            "h": "h",
            "hr": "ɦ"
        }
    },
    "lateral-fricative": {
        "dental": {
            "lf": "ɬ"
        },
        "post-alveolar": {
            "lz": "ɮ"
        }
    },
    "approximant": {
        "labio-dental": {
            "vr": "ʋ"
        },
        "post-alveolar": {
            "r": "ɹ"
        },
        "retroflex": {
            "rh": "ɻ"
        },
        "palatal": {
            "j": "j"
        },
        "velar": {
            "rw": "ɰ"
        }
    },
    "lateral-approximant": {
        "post-alveolar": {
            "l": "l"
        },
        "retroflex": {
            "lh": "ɭ"
        },
        "palatal": {
            "lj": "ʎ"
        },
        "velar": {
            "lw": "ʟ"
        }
    }
}

PULMONIC_CONSONANTS_TABLE = {
    "\u00e7": "fricative/palatal",
    "\u00f0": "fricative/dental",
    "\u0127": "fricative/pharyngeal",
    "\u014b": "nasal/velar",
    "\u0256": "plosive/retroflex",
    "\u025f": "plosive/palatal",
    "\u0262": "plosive/uvular",
    "\u0263": "fricative/velar",
    "\u0266": "fricative/glottal",
    "\u026c": "lateral-fricative/dental",
    "\u026d": "lateral-approximate/retroflex",
    "\u026e": "lateral-fricative/post-alveolar",
    "\u0270": "approximate/velar",
    "\u0271": "nasal/labio-dental",
    "\u0272": "nasal/palatal",
    "\u0273": "nasal/retroflex",
    "\u0274": "nasal/uvular",
    "\u0278": "fricative/bi-labial",
    "\u0279": "approximate/post-alveolar",
    "\u027b": "approximate/retroflex",
    "\u027d": "tap/retroflex",
    "\u027e": "tap/post-alveolar",
    "\u0280": "trill/uvular",
    "\u0281": "fricative/uvular",
    "\u0282": "fricative/retroflex",
    "\u0283": "fricative/post-alveolar",
    "\u0288": "plosive/retroflex",
    "\u028b": "approximate/labio-dental",
    "\u028e": "lateral-approximate/palatal",
    "\u0290": "fricative/retroflex",
    "\u0292": "fricative/post-alveolar",
    "\u0294": "plosive/glottal",
    "\u0295": "fricative/pharyngeal",
    "\u0299": "trill/bi-labial",
    "\u029d": "fricative/palatal",
    "\u029f": "lateral-approximate/velar",
    "\u03b2": "fricative/bi-labial",
    "\u03b8": "fricative/dental",
    "\u03c7": "fricative/uvular",
    "\u2c71": "tap/labio-dental",
    "b": "plosive/bi-labial",
    "c": "plosive/palatal",
    "d": "plosive/post-alveolar",
    "f": "fricative/labio-dental",
    "g": "plosive/velar",
    "h": "fricative/glottal",
    "j": "approximate/palatal",
    "k": "plosive/velar",
    "l": "lateral-approximate/post-alveolar",
    "m": "nasal/bi-labial",
    "n": "nasal/post-alveolar",
    "p": "plosive/bi-labial",
    "q": "plosive/uvular",
    "r": "trill/post-alveolar",
    "s": "fricative/alveolar",
    "t": "plosive/alveolar",
    "v": "fricative/labio-dental",
    "x": "fricative/velar",
    "z": "fricative/alveolar"
}

PULMONIC_CONSONANTS_LOOKUP = {
    "b": "b",
    "br": "\u0299",
    "c": "c",
    "cr": "\u025f",
    "cx": "\u00e7",
    "d": "d",
    "dr": "\u0256",
    "f": "f",
    "fg": "\u0295",
    "fh": "\u0127",
    "fr": "\u0281",
    "fx": "\u03c7",
    "g": "g",
    "gh": "\u0294",
    "gv": "\u0262",
    "h": "h",
    "hr": "\u0266",
    "j": "j",
    "jx": "\u029d",
    "k": "k",
    "kv": "q",
    "l": "l",
    "lf": "\u026c",
    "lh": "\u026d",
    "lj": "\u028e",
    "lw": "\u029f",
    "lz": "\u026e",
    "m": "m",
    "mn": "\u0271",
    "n": "n",
    "ng": "\u014b",
    "ng1": "\u0273",
    "ng2": "\u0272",
    "nh": "\u0274",
    "p": "p",
    "ph": "\u0278",
    "phv": "\u03b2",
    "r": "\u0279",
    "rf": "\u027d",
    "rh": "\u027b",
    "rr": "\u0280",
    "rt": "\u027e",
    "rw": "\u0270",
    "s": "s",
    "sh": "\u0283",
    "sr": "\u0282",
    "t": "t",
    "th": "\u03b8",
    "thv": "\u00f0",
    "tr": "\u0288",
    "v": "v",
    "vr": "\u028b",
    "vt": "\u2c71",
    "x": "x",
    "xz": "\u0263",
    "z": "z",
    "zh": "\u0292",
    "zr": "\u0290"
}

PULMONIC_CONSONANTS_LOOKUP_REVERSE = {v: k for k, v in PULMONIC_CONSONANTS_LOOKUP.items()}

NON_PULMONIC_CONSONANTS = {
}

NON_PULMONIC_CONSONANTS_TABLE = {
}

NON_PULMONIC_CONSONANTS_LOOKUP = {
}

NON_PULMONIC_CONSONANTS_LOOKUP_REVERSE = {v: k for k, v in NON_PULMONIC_CONSONANTS_LOOKUP.items()}

VOWELS = {
    "close": {
        "front": {
            "i": "i",
            "y": "y"
        },
        "central": {
            "iu": "ɨ",
            "uu": "ʉ"
        },
        "back": {
            "uv": "ɯ",
            "u": "u"
        }
    },
    "medial-close-mid": {
        "front": {
            "ie": "ɪ",
            "ye": "ʏ"
        },
        "back": {
            "ue": "ʊ"
        }
    },
    "close-mid": {
        "front": {
            "e": "e",
            "ey": "ø"
        },
        "central": {
            "eu": "ɘ",
            "uy": "ɵ"
        },
        "back": {
            "oe": "ɤ",
            "o": "o"
        }
    },
    "mid": {
        "central": {
            "uh": "ə"
        }
    },
    "open-mid": {
        "front": {
            "eh": "ɛ",
            "ehy": "œ"
        },
        "central": {
            "ea": "ɜ",
            "eay": "ɞ"
        },
        "back": {
            "uh": "ʌ",
            "uhy": "ɔ"
        }
    },
    "medial-open-mid": {
        "front": {
            "ae": "æ"
        },
        "central": {
            "ah": "ɐ"
        }
    },
    "open": {
        "front": {
            "a": "a",
            "ay": "ɶ"
        },
        "back": {
            "ao": "ɑ",
            "aoy": "ɒ"
        }
    }
}

VOWELS_TABLE = {
    "\u00e6": "medial-open-mid/front",
    "\u00f8": "close-mid/front",
    "\u0153": "open-mid/front",
    "\u0250": "medial-open-mid/central",
    "\u0251": "open/back",
    "\u0252": "open/back",
    "\u0254": "open-mid/back",
    "\u0258": "close-mid/central",
    "\u0259": "mid/central",
    "\u025b": "open-mid/front",
    "\u025c": "open-mid/central",
    "\u025e": "open-mid/central",
    "\u0264": "close-mid/back",
    "\u0268": "close/central",
    "\u026a": "medial-close-mid/front",
    "\u026f": "close/back",
    "\u0275": "close-mid/central",
    "\u0276": "open/front",
    "\u0289": "close/central",
    "\u028a": "medial-close-mid/back",
    "\u028c": "open-mid/back",
    "\u028f": "medial-close-mid/front",
    "a": "open/front",
    "e": "close-mid/front",
    "i": "close/front",
    "o": "close-mid/back",
    "u": "close/back",
    "y": "close/front"
}

VOWELS_LOOKUP = {
    "a": "a",
    "ae": "\u00e6",
    "ah": "\u0250",
    "ao": "\u0251",
    "aoy": "\u0252",
    "ay": "\u0276",
    "e": "e",
    "ea": "\u025c",
    "eay": "\u025e",
    "eh": "\u025b",
    "ehy": "\u0153",
    "eu": "\u0258",
    "ey": "\u00f8",
    "i": "i",
    "ie": "\u026a",
    "iu": "\u0268",
    "o": "o",
    "oe": "\u0264",
    "u": "u",
    "ue": "\u028a",
    "uh": "\u028c",
    "uhy": "\u0254",
    "uu": "\u0289",
    "uv": "\u026f",
    "uy": "\u0275",
    "y": "y",
    "ye": "\u028f"
}

VOWELS_LOOKUP_REVERSE = {v: k for k, v in VOWELS_LOOKUP.items()}

__all__ = [
    "PULMONIC_CONSONANTS",
    "PULMONIC_CONSONANTS_TABLE",
    "PULMONIC_CONSONANTS_LOOKUP",
    "VOWELS",
    "VOWELS_TABLE",
    "VOWELS_LOOKUP"
]
