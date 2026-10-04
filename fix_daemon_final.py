import re

path = r"D:\ultron\ultron_daemon.py"
with open(path, "r", encoding="utf-8") as f:
    code = f.read()

# Define has_en at the start of listen_loop
if "def listen_loop():" in code:
    code = code.replace("def listen_loop():\n    global GUI_PROCESS", "def listen_loop():\n    global GUI_PROCESS\n    has_en = False")

# Inject the model load after rec = KaldiRecognizer(model, 16000)
old_init_regex = r"rec\s*=\s*KaldiRecognizer\(model,\s*16000\)"
new_init = """rec = KaldiRecognizer(model, 16000)
        try:
            import os
            MODEL_PATH_EN = os.path.abspath(os.path.join(os.path.dirname(__file__), 'vosk-model-en'))
            model_en = Model(MODEL_PATH_EN)
            rec_en = KaldiRecognizer(model_en, 16000)
            has_en = True
        except Exception as e:
            has_en = False
            print("English model error:", e)"""
code = re.sub(old_init_regex, new_init, code, count=1)

with open(path, "w", encoding="utf-8") as f:
    f.write(code)
print("Daemon finally patched.")
