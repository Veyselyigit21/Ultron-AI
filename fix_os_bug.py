path = r"D:\ultron\ultron_daemon.py"
with open(path, "r", encoding="utf-8") as f:
    code = f.read()

code = code.replace("try:\n            import os\n            MODEL_PATH_EN", "try:\n            MODEL_PATH_EN")

with open(path, "w", encoding="utf-8") as f:
    f.write(code)
print("ultron_daemon.py os local degisken hatasi duzeltildi!")

path2 = r"D:\ultron\senses\background_ear.py"
with open(path2, "r", encoding="utf-8") as f:
    code2 = f.read()
if "import os\n" in code2.split("try:")[1][:50]:  # Just a safety check, I didn't inject import os here
    pass
