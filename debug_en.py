path = r"D:\ultron\ultron_daemon.py"
with open(path, "r", encoding="utf-8") as f:
    code = f.read()

old_wake = """            if not is_wake and has_en:
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

new_wake = """            if not is_wake and has_en:
                if is_final_en:
                    text_en = json.loads(rec_en.Result()).get('text', '').lower().strip()
                else:
                    text_en = json.loads(rec_en.PartialResult()).get('partial', '').lower().strip()

                if text_en and "ultron" not in text_en and "altron" not in text_en:
                    with open("D:/ultron/daemon_words.log", "a", encoding="utf-8") as f:
                        f.write("[EN Duyuldu] " + text_en + "\\n")

                if "ultron" in text_en or "altron" in text_en or "ltron" in text_en or "outrun" in text_en or "eltron" in text_en:
                    is_wake = True
                    text = text_en"""

code = code.replace(old_wake, new_wake)

with open(path, "w", encoding="utf-8") as f:
    f.write(code)
print("Debug English logic injected!")
