import difflib

def is_similar(word, target="ultron"):
    return difflib.SequenceMatcher(None, word, target).ratio()

words = ["ultron", "altron", "outrun", "old run", "uç rol", "turan", "botu", "otur", "or drawn", "oh wrong", "voltran", "uykusu", "atron", "otron", "antro", "ultra", "ltron"]
for w in words:
    print(f"{w}: {is_similar(w, 'ultron'):.2f}")
