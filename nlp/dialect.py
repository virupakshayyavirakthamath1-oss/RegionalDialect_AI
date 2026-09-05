import re


DIALECT_MARKERS = {
    "Kanglish": [
        "maga",
        "guru",
        "swalpa",
        "yen",
        "enu",
        "illa",
        "hogbeku",
        "bartini",
        "madbeku",
        "mane",
        "office ge",
        "college ge",
        "andre",
        "yaake",
        "hege",
    ],

    "Hinglish": [
        "yaar",
        "bhai",
        "mujhe",
        "mere",
        "kal",
        "aaj",
        "jana",
        "jaana",
        "karna",
        "karo",
        "hai",
        "nahi",
        "nahin",
        "accha",
        "acha",
        "kya",
        "kaise",
        "wala",
        "wali",
    ],

    "Tanglish": [
        "macha",
        "semma",
        "enna",
        "epdi",
        "romba",
        "illa",
        "venum",
        "pannunga",
        "pannitu",
        "poitu",
        "saptiya",
        "da",
        "di",
        "inga",
        "anga",
    ],
}


def detect_dialect(text):
    """
    Detect whether the text looks like Kanglish,
    Hinglish, Tanglish, or mixed/English.
    """

    if text is None:
        text = ""

    text = str(text).strip()
    t = text.lower()

    scores = {}

    for dialect, markers in DIALECT_MARKERS.items():
        hits = 0

        for marker in markers:
            marker = marker.lower().strip()

            if not marker:
                continue

            # Handle multi-word markers such as "office ge"
            if " " in marker:
                if marker in t:
                    hits += 1

            # Handle normal words
            else:
                pattern = r"(?<!\w)" + re.escape(marker) + r"(?!\w)"

                if re.search(pattern, t):
                    hits += 1

        scores[dialect] = hits

    total = sum(scores.values())

    if total == 0:
        return {
            "dialect": "Mixed / English",
            "confidence": 52.0,
            "scores": scores,
        }

    best = max(scores, key=scores.get)

    # If two or more dialects have the same highest score,
    # classify as mixed instead of arbitrarily selecting one.
    highest = scores[best]

    winners = [
        dialect
        for dialect, score in scores.items()
        if score == highest
    ]

    if len(winners) > 1:
        confidence = 55.0 + (highest / max(total, 1)) * 20.0

        return {
            "dialect": "Mixed",
            "confidence": round(min(90.0, confidence), 1),
            "scores": scores,
        }

    confidence = 55.0 + (highest / max(total, 1)) * 43.0

    return {
        "dialect": best,
        "confidence": round(min(98.0, confidence), 1),
        "scores": scores,
    }