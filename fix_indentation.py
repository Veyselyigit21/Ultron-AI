path = r"D:\ultron\main_gui.py"
with open(path, "r", encoding="utf-8") as f:
    code = f.read()

# I will just remove send_real_stats from the middle of __init__
import re
# First, revert the injection in __init__
code = re.sub(r"        self\.stats_timer = QTimer\(\)\n.*?except Exception as e:\n            pass\n", "", code, flags=re.DOTALL)

# Now, cleanly add the timer to __init__ at the end of __init__
init_end = "QTimer.singleShot(800, self.startup_routine)"
init_fixed = """QTimer.singleShot(800, self.startup_routine)
        
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self.send_real_stats)
        self.stats_timer.start(2000)"""

code = code.replace(init_end, init_fixed)

# Now, cleanly add send_real_stats as a method of UltronGUI
method = """
    def send_real_stats(self):
        try:
            import psutil
            cpu = int(psutil.cpu_percent())
            ram = int(psutil.virtual_memory().percent)
            gpu = 0
            js = f"if(typeof updateRealStats === 'function') updateRealStats({cpu}, {ram}, {gpu});"
            self.browser.page().runJavaScript(js)
        except Exception as e:
            pass
"""

# add it before wake_window
code = code.replace("    def wake_window(self):", method + "\n    def wake_window(self):")

with open(path, "w", encoding="utf-8") as f:
    f.write(code)
print("Indentation and infinite loop fixed!")
