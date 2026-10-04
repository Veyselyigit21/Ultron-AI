import re

path = r"D:\ultron\ultron_daemon.py"
with open(path, "r", encoding="utf-8") as f:
    code = f.read()

# Fix wake word logic to use English model
old_wake_regex = r"words\s*=\s*text\.split\(\)\s*is_wake\s*=\s*any\(word\.startswith\(w\)\s*for\s*word\s*in\s*words\s*for\s*w\s*in\s*WAKE_WORDS\)"

new_wake = """words = text.split()
            is_wake = any(word.startswith(w) for word in words for w in WAKE_WORDS)
            
            if not is_wake and has_en:
                partial_en = json.loads(rec_en.PartialResult())
                text_en = partial_en.get('partial', '').lower().strip()
                if "ultron" in text_en or "altron" in text_en:
                    is_wake = True
                    text = text_en"""

code = re.sub(old_wake_regex, new_wake, code, count=1)

with open(path, "w", encoding="utf-8") as f:
    f.write(code)
print("Daemon finally patched with english wake logic!")
