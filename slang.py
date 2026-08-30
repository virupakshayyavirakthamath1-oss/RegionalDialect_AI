SLANG = {
    "maga": {"dialect": "Kanglish", "meaning": "friend / bro", "formal": "friend"},
    "guru": {"dialect": "Kanglish", "meaning": "friend / mate", "formal": "friend"},
    "swalpa": {"dialect": "Kanglish", "meaning": "a little", "formal": "a little"},
    "yaar": {"dialect": "Hinglish", "meaning": "friend / buddy", "formal": "friend"},
    "bhai": {"dialect": "Hinglish", "meaning": "brother / bro", "formal": "friend / brother"},
    "accha": {"dialect": "Hinglish", "meaning": "okay / good", "formal": "okay"},
    "macha": {"dialect": "Tanglish", "meaning": "friend / bro", "formal": "friend"},
    "semma": {"dialect": "Tanglish", "meaning": "very / excellent", "formal": "very good"},
    "da": {"dialect": "Tanglish", "meaning": "informal address", "formal": "friend"},
    "di": {"dialect": "Tanglish", "meaning": "informal address", "formal": "friend"},
}


def get_slang_dictionary():
    return SLANG


def detect_slang(text, custom=None):
    data = dict(SLANG)
    if custom:
        data.update(custom)
    found = []
    for word, info in data.items():
        if __import__('re').search(r"(?<!\w)" + __import__('re').escape(word) + r"(?!\w)", text.lower()):
            item = {"word": word, **info}
            found.append(item)
    return found
