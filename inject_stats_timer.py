path = r"D:\ultron\main_gui.py"
with open(path, "r", encoding="utf-8") as f:
    code = f.read()

old_init = "self.browser.page().setBackgroundColor(Qt.GlobalColor.black)"
new_init = """self.browser.page().setBackgroundColor(Qt.GlobalColor.black)

        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self.send_real_stats)
        self.stats_timer.start(2000)

    def send_real_stats(self):
        try:
            cpu = int(psutil.cpu_percent())
            ram = int(psutil.virtual_memory().percent)
            gpu = 0
            js = f"if(typeof updateRealStats === 'function') updateRealStats({cpu}, {ram}, {gpu});"
            self.browser.page().runJavaScript(js)
        except Exception as e:
            pass"""

if "def send_real_stats" not in code:
    code = code.replace(old_init, new_init)

with open(path, "w", encoding="utf-8") as f:
    f.write(code)
print("Real stats timer injected!")
