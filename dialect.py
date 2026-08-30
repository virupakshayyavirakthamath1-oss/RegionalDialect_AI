import re

DIALECT_MARKERS = {
    "Kanglish": ["maga", "guru", "swalpa", "yen", "enu", "illa", "hogbeku", "bartini", "madbeku", "mane", "office ge", "college ge", "andre", "yaake", "hege"],
    "Hinglish": ["yaar", "bhai", "mujhe", "mere", "kal", "aaj", "jana", "jaana", "karna", "karo", "hai", "nahi", "nahin", "accha", "acha", "kya", "kaise", "wala", "wali"],
    "Tanglish": ["macha", "semma", "enna", "epdi", "romba", "illa", "venum", "pannunga", "pannitu", "poitu", "saptiya", "da", "di", "inga", "anga"],
}


def detect_dialect(text):
    t = text.lower()
    scores = {}
    for dialect, markers in DIALECT_MARKERS.items():
        hits = 0
        for marker in markers:
            if re.search(r"(?<!\w)" + re.escape(marker) + r"(?!\w)", t):
                hits += 1
            elif " " in marker and marker in t:
                hits += 1
        scores[dialect] = hits
    best = max(scores, key=scores.get) if scores else "Mixed"
    total = sum(scores.values())
    if total == 0:
        return {"dialect": "Mixed / English", "confidence": 52.0, "scores": scores}
    confidence = min(98.0, 55.0 + (scores[best] / max(total, 1)) * 43.0)
    return {"dialect": best, "confidence": round(confidence, 1), "scores": scores}
