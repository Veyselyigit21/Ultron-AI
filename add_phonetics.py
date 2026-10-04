path1 = r"D:\ultron\ultron_daemon.py"
path2 = r"D:\ultron\senses\background_ear.py"

for p in [path1, path2]:
    with open(p, "r", encoding="utf-8") as f:
        code = f.read()
    
    # Update English phonetics
    old_en = '["ultron", "altron", "ltron", "outrun", "eltron", "old run", "all drawn", "all drawn on"]'
    new_en = '["ultron", "altron", "ltron", "outrun", "eltron", "old run", "all drawn", "all drawn on", "oh drawn", "oh wrong"]'
    
    code = code.replace(old_en, new_en)
    
    # Fallback for background_ear that didn't have the full list
    if "oh drawn" not in code:
        code = code.replace('["ultron", "altron", "ltron", "outrun", "eltron"]', new_en)
    
    # Update Turkish phonetics
    old_tr = '["ultron", "ultra", "ultran", "altron", "oltron", "ultra an", "altran", "akron", "uran", "atron", "otron", "antro", "voltran"]'
    new_tr = '["ultron", "ultra", "ultran", "altron", "oltron", "ultra an", "altran", "akron", "uran", "atron", "otron", "antro", "voltran", "uç rol", "uykusu rol", "uçurol", "uçu rol"]'
    code = code.replace(old_tr, new_tr)

    with open(p, "w", encoding="utf-8") as f:
        f.write(code)

print("Phonetics injected!")
