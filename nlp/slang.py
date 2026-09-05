import re
SLANG_DICTIONARY = {
    "Kanglish": {
        "maga": {
            "meaning": "friend / brother",
            "formal": "friend",
        },
        "guru": {
            "meaning": "friend / buddy",
            "formal": "friend",
        },
        "swalpa": {
            "meaning": "a little",
            "formal": "a little",
        },
        "yen": {
            "meaning": "what",
            "formal": "what",
        },
        "enu": {
            "meaning": "what",
            "formal": "what",
        },
        "illa": {
            "meaning": "no / not",
            "formal": "no",
        },
        "yaake": {
            "meaning": "why",
            "formal": "why",
        },
    },

    "Hinglish": {
        "yaar": {
            "meaning": "friend / buddy",
            "formal": "friend",
        },
        "bhai": {
            "meaning": "brother / friend",
            "formal": "friend",
        },
        "mujhe": {
            "meaning": "to me",
            "formal": "to me",
        },
        "aaj": {
            "meaning": "today",
            "formal": "today",
        },
        "kal": {
            "meaning": "yesterday / tomorrow",
            "formal": "depending on context",
        },
        "nahi": {
            "meaning": "no / not",
            "formal": "not",
        },
        "accha": {
            "meaning": "good / okay",
            "formal": "good",
        },
        "kya": {
            "meaning": "what",
            "formal": "what",
        },
        "kaise": {
            "meaning": "how",
            "formal": "how",
        },
    },

    "Tanglish": {
        "macha": {
            "meaning": "friend / buddy",
            "formal": "friend",
        },
        "semma": {
            "meaning": "excellent / very good",
            "formal": "excellent",
        },
        "enna": {
            "meaning": "what",
            "formal": "what",
        },
        "epdi": {
            "meaning": "how",
            "formal": "how",
        },
        "romba": {
            "meaning": "very / much",
            "formal": "very",
        },
        "illa": {
            "meaning": "no / not",
            "formal": "no",
        },
        "venum": {
            "meaning": "want / need",
            "formal": "need",
        },
        "da": {
            "meaning": "informal address",
            "formal": "",
        },
        "di": {
            "meaning": "informal address",
            "formal": "",
        },
        "inga": {
            "meaning": "here",
            "formal": "here",
        },
        "anga": {
            "meaning": "there",
            "formal": "there",
        },
    },
}


def get_slang_dictionary():
    """
    Return the complete slang dictionary in a format
    that can be used by the Flask templates.
    """

    result = []

    for dialect, words in SLANG_DICTIONARY.items():
        for word, info in words.items():
            result.append({
                "word": word,
                "meaning": info.get("meaning", ""),
                "formal": info.get("formal", ""),
                "dialect": dialect,
            })

    return result


def detect_slang(text):
    """
    Detect slang words in the supplied text.
    """

    if text is None:
        text = ""

    text = str(text).lower()

    detected = []

    for dialect, words in SLANG_DICTIONARY.items():
        for word, info in words.items():

            pattern = r"(?<!\w)" + re.escape(word) + r"(?!\w)"

            if re.search(pattern, text):
                detected.append({
                    "word": word,
                    "meaning": info.get("meaning", ""),
                    "formal": info.get("formal", ""),
                    "dialect": dialect,
                })

    return detected