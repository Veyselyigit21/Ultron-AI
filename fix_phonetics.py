path = r"D:\ultron\senses\background_ear.py"
with open(path, "r", encoding="utf-8") as f:
    code = f.read()

old_list = '["ultron", "altron", "ltron", "outrun", "eltron"]'
new_list = '["ultron", "altron", "ltron", "outrun", "eltron", "old run", "all drawn", "all drawn on"]'

code = code.replace(old_list, new_list)

with open(path, "w", encoding="utf-8") as f:
    f.write(code)
print("background_ear.py updated with phonetic wake words!")
