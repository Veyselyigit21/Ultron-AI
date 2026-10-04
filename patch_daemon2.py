import os

path = r"D:\ultron\ultron_daemon.py"
with open(path, "r", encoding="utf-8") as f:
    code = f.read()

# Fix init
old_init = """        model = Model(model_path)
        rec = KaldiRecognizer(model, 16000)"""
new_init = """        model = Model(model_path)
        rec = KaldiRecognizer(model, 16000)
        
        try:
            MODEL_PATH_EN = os.path.abspath(os.path.join(os.path.dirname(__file__), 'vosk-model-en'))
            model_en = Model(MODEL_PATH_EN)
            rec_en = KaldiRecognizer(model_en, 16000)
            has_en = True
        except:
            has_en = False"""
if "has_en = True" not in code:
    code = code.replace(old_init, new_init)

# Fix loop
old_loop = """            is_final = rec.AcceptWaveform(data)

            if is_final:"""
new_loop = """            is_final = rec.AcceptWaveform(data)
            if has_en:
                rec_en.AcceptWaveform(data)

            if is_final:"""
if "rec_en.AcceptWaveform(data)" not in code:
    code = code.replace(old_loop, new_loop)

# Fix wake logic
old_wake = """            else:
                partial = json.loads(rec.PartialResult())
                text = partial.get('partial', '').lower().strip()
                if not text:
                    continue
                
                words = text.split()
                is_wake = any(word.startswith(w) for word in words for w in WAKE_WORDS)

                if is_wake:"""
new_wake = """            else:
                partial = json.loads(rec.PartialResult())
                text = partial.get('partial', '').lower().strip()
                
                is_wake = False
                if text:
                    words = text.split()
                    is_wake = any(word.startswith(w) for word in words for w in WAKE_WORDS)
                    
                if not is_wake and has_en:
                    partial_en = json.loads(rec_en.PartialResult())
                    text_en = partial_en.get('partial', '').lower().strip()
                    if "ultron" in text_en or "altron" in text_en:
                        is_wake = True
                        text = text_en

                if is_wake:"""
if "partial_en = json.loads(rec_en.PartialResult())" not in code:
    code = code.replace(old_wake, new_wake)

with open(path, "w", encoding="utf-8") as f:
    f.write(code)
print("ultron_daemon.py basariyla guncellendi!")
