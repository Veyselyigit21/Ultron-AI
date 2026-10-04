path1 = r"D:\ultron\ultron_daemon.py"
path2 = r"D:\ultron\senses\background_ear.py"

for p in [path1, path2]:
    with open(p, "r", encoding="utf-8") as f:
        code = f.read()
    
    # Add prefixed wake words
    old_tr = '["ultron", "ultra", "ultran", "altron", "oltron", "ultra an", "altran", "akron", "uran", "atron", "otron", "antro", "voltran", "uç rol", "uykusu rol", "uçurol", "uçu rol", "turan", "o çukura", "botu"]'
    new_tr = '["hey ultron", "merhaba ultron", "ultron uyan", "ultron dinle", "ultron açıl", "ultron", "ultra", "ultran", "altron", "oltron", "ultra an", "altran", "akron", "uran", "atron", "otron", "antro", "voltran", "uç rol", "uykusu rol", "uçurol", "uçu rol", "turan", "o çukura", "botu"]'
    code = code.replace(old_tr, new_tr)

    with open(p, "w", encoding="utf-8") as f:
        f.write(code)

print("Prefixed wake words added!")
