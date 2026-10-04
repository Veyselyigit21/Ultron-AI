path = r"D:\ultron\ultron_daemon.py"
with open(path, "r", encoding="utf-8") as f:
    code = f.read()

code = code.replace('"venv", "Scripts", "python.exe"', '"venv", "Scripts", "pythonw.exe"')

with open(path, "w", encoding="utf-8") as f:
    f.write(code)
print("Tray menusu pythonw olarak guncellendi")
