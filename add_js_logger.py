path = r"D:\ultron\main_gui.py"
with open(path, "r", encoding="utf-8") as f:
    code = f.read()

new_class = """from PyQt6.QtWebEngineCore import QWebEnginePage
class CustomWebPage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        with open("D:/ultron/js_console.log", "a", encoding="utf-8") as f:
            f.write(f"[{level}] {message} (Line {lineNumber})\\n")
        super().javaScriptConsoleMessage(level, message, lineNumber, sourceID)

"""

if "class CustomWebPage" not in code:
    code = code.replace("class Backend(QObject):", new_class + "class Backend(QObject):")

old_page = "self.browser = QWebEngineView()"
new_page = """self.browser = QWebEngineView()
        self.custom_page = CustomWebPage(self.browser)
        self.browser.setPage(self.custom_page)"""

if "self.custom_page" not in code:
    code = code.replace(old_page, new_page)

with open(path, "w", encoding="utf-8") as f:
    f.write(code)
print("WebEngine JS Logger added!")
