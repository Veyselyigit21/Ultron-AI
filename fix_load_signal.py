path = r"D:\ultron\main_gui.py"
with open(path, "r", encoding="utf-8") as f:
    code = f.read()

old_timer = "QTimer.singleShot(100, lambda: self.browser.page().runJavaScript('triggerWakeAnimation();'))"
new_timer = "self.browser.loadFinished.connect(lambda ok: self.browser.page().runJavaScript('triggerWakeAnimation();'))"

code = code.replace(old_timer, new_timer)

with open(path, "w", encoding="utf-8") as f:
    f.write(code)
print("loadFinished signal connected!")
