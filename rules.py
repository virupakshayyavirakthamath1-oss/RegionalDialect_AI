import re

RULES = [
    (r"\bi am go\b", "I am going", "Grammar", "Use 'I am going' for a natural present-progressive sentence."),
    (r"\bi is\b", "I am", "Grammar", "The subject 'I' takes 'am'."),
    (r"\bhe go\b", "he goes", "Grammar", "Third-person singular verbs usually take -s in the simple present."),
    (r"\bshe go\b", "she goes", "Grammar", "Third-person singular verbs usually take -s in the simple present."),
    (r"\bthey is\b", "they are", "Grammar", "Use 'are' with 'they'."),
    (r"\bwe is\b", "we are", "Grammar", "Use 'are' with 'we'."),
    (r"\byesterday i go\b", "yesterday I went", "Grammar", "Use the past tense after 'yesterday'."),
    (r"\bmore better\b", "better", "Grammar", "Avoid the double comparative 'more better'."),
    (r"\bvery unique\b", "unique", "Style", "'Unique' is normally used without 'very'."),
]


def apply_rules(text):
    corrected = text
    errors = []
    for pattern, replacement, kind, explanation in RULES:
        match = re.search(pattern, corrected, flags=re.IGNORECASE)
        if match:
            original = match.group(0)
            corrected = re.sub(pattern, replacement, corrected, count=1, flags=re.IGNORECASE)
            errors.append({"type": kind, "original": original, "suggestion": replacement, "explanation": explanation})
    if corrected and corrected[0].islower():
        fixed = corrected[0].upper() + corrected[1:]
        if fixed != corrected:
            errors.append({"type": "Capitalization", "original": corrected[0], "suggestion": fixed[0], "explanation": "Start a sentence with a capital letter."})
            corrected = fixed
    if corrected and corrected[-1] not in ".!?":
        errors.append({"type": "Punctuation", "original": "(missing)", "suggestion": ".", "explanation": "Add punctuation at the end of a complete sentence."})
        corrected += "."
    return corrected, errors
