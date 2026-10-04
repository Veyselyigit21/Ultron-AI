path = r"D:\ultron\main_gui.py"
with open(path, "r", encoding="utf-8") as f:
    code = f.read()

code = code.replace("self.mic_volume_changed.emit(float(vol))", "self.mic_volume_changed.emit(float(vol) / 25.0)")

with open(path, "w", encoding="utf-8") as f:
    f.write(code)
print("GUI volume scalar updated!")
