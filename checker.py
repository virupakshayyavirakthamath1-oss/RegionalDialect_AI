from rules import check_grammar
from nlp.dialect import detect_dialect
from nlp.slang import detect_slang


def check_text(text, selected_dialect="Auto", user_id=None, db_path=None):

    # Grammar checking
    grammar_result = check_grammar(text)

    # Dialect detection
    detected = detect_dialect(text)

    if selected_dialect and selected_dialect != "Auto":
        dialect = selected_dialect
    else:
        dialect = detected["dialect"]

    # Slang detection
    slang = detect_slang(text)

    # Calculate score
    error_count = len(grammar_result["errors"])
    slang_count = len(slang)

    score = 100

    score -= error_count * 8
    score -= slang_count * 3

    score = max(0, min(100, score))

    return {
        "original": text,
        "correction": grammar_result["correction"],
        "errors": grammar_result["errors"],
        "slang": slang,
        "dialect": dialect,
        "dialect_confidence": detected["confidence"],
        "dialect_scores": detected["scores"],
        "overall_score": score,
    }