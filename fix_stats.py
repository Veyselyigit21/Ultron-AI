import re

path = r"D:\ultron\main_gui.py"
with open(path, "r", encoding="utf-8") as f:
    code = f.read()

if "import psutil" not in code:
    code = code.replace("import sys", "import sys\nimport psutil")

old_init = "        self.browser.page().setBackgroundColor(QColor(0, 0, 0, 0))"
new_init = """        self.browser.page().setBackgroundColor(QColor(0, 0, 0, 0))

        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self.send_real_stats)
        self.stats_timer.start(2000)

    def send_real_stats(self):
        try:
            cpu = int(psutil.cpu_percent())
            ram = int(psutil.virtual_memory().percent)
            # GPU fake for now unless pynvml is installed
            gpu = 0
            js = f"if(typeof updateRealStats === 'function') updateRealStats({cpu}, {ram}, {gpu});"
            self.browser.page().runJavaScript(js)
        except: pass"""

if "def send_real_stats" not in code:
    code = code.replace(old_init, new_init)

with open(path, "w", encoding="utf-8") as f:
    f.write(code)

path2 = r"D:\ultron\gui\index_v2.html"
with open(path2, "r", encoding="utf-8") as f:
    html = f.read()

old_js_stats = """    const cpu = Math.floor(Math.random() * 15 + 8);
    const ram = Math.floor(Math.random() * 5  + 40);
    const gpu = Math.floor(Math.random() * 10 + 4);
    document.getElementById('cpu-val').textContent = cpu + '%';
    document.getElementById('cpu-bar').style.width  = cpu + '%';
    document.getElementById('ram-val').textContent = ram + '%';
    document.getElementById('ram-bar').style.width  = ram + '%';
    document.getElementById('gpu-val').textContent = gpu + '%';
    document.getElementById('gpu-bar').style.width  = gpu + '%';"""
    
new_js_stats = """// Real stats updated via python updateRealStats()"""
html = html.replace(old_js_stats, new_js_stats)

update_fn = """function updateRealStats(cpu, ram, gpu) {
    document.getElementById('cpu-val').textContent = cpu + '%';
    document.getElementById('cpu-bar').style.width  = cpu + '%';
    document.getElementById('ram-val').textContent = ram + '%';
    document.getElementById('ram-bar').style.width  = ram + '%';
    document.getElementById('gpu-val').textContent = gpu + '%';
    document.getElementById('gpu-bar').style.width  = gpu + '%';
}
"""
if "function updateRealStats" not in html:
    html = html.replace("function frame() {", update_fn + "\nfunction frame() {")

with open(path2, "w", encoding="utf-8") as f:
    f.write(html)
print("Real stats injected!")
