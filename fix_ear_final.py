import re

path = r"D:\ultron\senses\background_ear.py"
with open(path, "r", encoding="utf-8") as f:
    code = f.read()

# Replace the wake logic
old_wake_regex = r"words\s*=\s*text\.split\(\)\s*is_wake\s*=\s*any\(word\.startswith\(w\)\s*for\s*word\s*in\s*words\s*for\s*w\s*in\s*WAKE_WORDS\)"

new_wake = """words = text.split()
                    is_wake = any(word.startswith(w) for word in words for w in WAKE_WORDS)
                    
                    if not is_wake and has_en:
                        if is_final_en:
                            text_en = json.loads(rec_en.Result()).get('text', '').lower().strip()
                        else:
                            text_en = json.loads(rec_en.PartialResult()).get('partial', '').lower().strip()
                        
                        if "ultron" in text_en or "altron" in text_en or "ltron" in text_en or "outrun" in text_en or "eltron" in text_en:
                            is_wake = True
                            text = text_en"""

code = re.sub(old_wake_regex, new_wake, code, count=1)

old_loop_regex = r"is_final\s*=\s*rec\.AcceptWaveform\(data\)"
new_loop = """is_final = rec.AcceptWaveform(data)
                is_final_en = False
                if has_en:
                    is_final_en = rec_en.AcceptWaveform(data)"""

code = re.sub(old_loop_regex, new_loop, code, count=1)

with open(path, "w", encoding="utf-8") as f:
    f.write(code)
print("background_ear.py fully patched!")
