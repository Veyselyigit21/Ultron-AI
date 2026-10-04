path1 = r"D:\ultron\ultron_daemon.py"
path2 = r"D:\ultron\senses\background_ear.py"

for p in [path1, path2]:
    with open(p, "r", encoding="utf-8") as f:
        code = f.read()
    
    # Update Turkish WAKE_WORDS
    old_words = 'WAKE_WORDS = ["ultron", "ultra", "ultran", "altron", "oltron", "ultra an", "altran", "akron", "uran", "atron", "otron", "antro", "altin"]'
    new_words = 'WAKE_WORDS = ["ultron", "ultra", "ultran", "altron", "oltron", "ultra an", "altran", "akron", "uran", "atron", "otron", "antro", "altin", "oturan", "bodrum", "voltran"]'
    code = code.replace(old_words, new_words)
    
    # Update English string check
    old_en = 'if "ultron" in text_en or "altron" in text_en or "ltron" in text_en or "outrun" in text_en or "eltron" in text_en:'
    new_en = 'if "ultron" in text_en or "altron" in text_en or "ltron" in text_en or "outrun" in text_en or "eltron" in text_en or "old run" in text_en or "all drawn" in text_en or "what\'s wrong" in text_en or "what is wrong" in text_en:'
    code = code.replace(old_en, new_en)
    
    with open(p, "w", encoding="utf-8") as f:
        f.write(code)

print("Wake words guncellendi!")
