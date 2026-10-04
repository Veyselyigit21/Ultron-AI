import re

path = r"D:\ultron\ultron_daemon.py"
with open(path, "r", encoding="utf-8") as f:
    code = f.read()

# Fix the English text extraction
old_wake = """            if not is_wake and has_en:
                partial_en = json.loads(rec_en.PartialResult())
                text_en = partial_en.get('partial', '').lower().strip()
                if "ultron" in text_en or "altron" in text_en:
                    is_wake = True
                    text = text_en"""

new_wake = """            if not is_wake and has_en:
                # Hem final hem partial result'u kontrol et
                res_en = json.loads(rec_en.FinalResult() if is_final_en else rec_en.PartialResult())
                text_en = res_en.get('text', res_en.get('partial', '')).lower().strip()
                
                # Eger FinalResult aldiktan sonra bostaysa, belki onceden is_final_en olmustur,
                # rec_en.Result() ile cekelim
                if not text_en:
                    res_en2 = json.loads(rec_en.Result())
                    text_en = res_en2.get('text', res_en2.get('partial', '')).lower().strip()
                    
                if "ultron" in text_en or "altron" in text_en:
                    is_wake = True
                    text = text_en"""

code = code.replace(old_wake, new_wake)

old_loop = """            is_final = rec.AcceptWaveform(data)
            if has_en:
                rec_en.AcceptWaveform(data)"""

new_loop = """            is_final = rec.AcceptWaveform(data)
            is_final_en = False
            if has_en:
                is_final_en = rec_en.AcceptWaveform(data)"""

code = code.replace(old_loop, new_loop)

with open(path, "w", encoding="utf-8") as f:
    f.write(code)

# Same for background_ear.py
path2 = r"D:\ultron\senses\background_ear.py"
with open(path2, "r", encoding="utf-8") as f:
    code2 = f.read()

old_wake2 = """                    if not is_wake and has_en:
                        partial_en = json.loads(rec_en.PartialResult())
                        text_en = partial_en.get('partial', '').lower().strip()
                        if "ultron" in text_en or "altron" in text_en:
                            is_wake = True
                            text = text_en"""

new_wake2 = """                    if not is_wake and has_en:
                        res_en = json.loads(rec_en.FinalResult() if is_final_en else rec_en.PartialResult())
                        text_en = res_en.get('text', res_en.get('partial', '')).lower().strip()
                        if not text_en:
                            res_en2 = json.loads(rec_en.Result())
                            text_en = res_en2.get('text', res_en2.get('partial', '')).lower().strip()
                        if "ultron" in text_en or "altron" in text_en:
                            is_wake = True
                            text = text_en"""
code2 = code2.replace(old_wake2, new_wake2)
code2 = code2.replace(old_loop, new_loop)

with open(path2, "w", encoding="utf-8") as f:
    f.write(code2)

print("English logic fixed!")
