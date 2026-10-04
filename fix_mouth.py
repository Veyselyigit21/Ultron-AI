path = r"D:\ultron\main_gui.py"
with open(path, "r", encoding="utf-8") as f:
    code = f.read()

code = code.replace("self.backend.mouth.speak(", "self.mouth.speak(")

with open(path, "w", encoding="utf-8") as f:
    f.write(code)
print("Fixed self.mouth")
