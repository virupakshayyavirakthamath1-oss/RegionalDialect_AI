import json
import re
import sqlite3
from dialect import detect_dialect
from rules import check_grammar
from slang import detect_slang


def _custom_words(db_path, user_id):
    if not user_id:
        return {}
    try:
        conn = sqlite3.connect(db_path)
        rows = conn.execute("SELECT word, meaning, dialect FROM dictionary WHERE user_id=?", (user_id,)).fetchall()
        conn.close()
        return {w: {"dialect": d, "meaning": m, "formal": m} for w, m, d in rows}
    except sqlite3.Error:
        return {}


def check_text(text, requested="Auto", user_id=None, db_path=None):
    normalized = re.sub(r"\s+", " ", text.strip())
    detection = detect_dialect(normalized)
    dialect = detection["dialect"] if requested == "Auto" else requested
    custom = _custom_words(db_path, user_id) if db_path else {}
    slang = detect_slang(normalized, custom)
    correction, errors = apply_rules(normalized)
    words = len(re.findall(r"\b[\w']+\b", normalized))
    grammar_score = max(0, round(100 - len(errors) * 10, 1))
    slang_score = max(0, round(100 - len(slang) * 4, 1))
    overall = round(grammar_score * 0.55 + detection["confidence"] * 0.30 + slang_score * 0.15, 1)
    return {
        "input_text": text,
        "normalized_text": normalized,
        "dialect": dialect,
        "auto_detected": detection["dialect"],
        "confidence": detection["confidence"],
        "scores": detection["scores"],
        "grammar_score": grammar_score,
        "slang_score": slang_score,
        "overall_score": overall,
        "errors": errors,
        "slang": slang,
        "correction": correction,
        "words": words,
        "status": "Potential improvements found." if errors else "No major grammar issue detected.",
        "note": "Hybrid NLP baseline: dialect markers + grammar rules + regional slang dictionary. Replace or extend these modules with a fine-tuned Transformer trained on your custom corpus for research evaluation."
    }
