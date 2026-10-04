path = r"D:\ultron\gui\index_v2.html"
with open(path, "r", encoding="utf-8") as f:
    html = f.read()

# Add window.onload trigger
onload_code = """
window.onload = function() {
    triggerWakeAnimation();
};
"""
if "window.onload" not in html:
    html = html.replace("function triggerWakeAnimation() {", onload_code + "function triggerWakeAnimation() {")

with open(path, "w", encoding="utf-8") as f:
    f.write(html)

path2 = r"D:\ultron\main_gui.py"
with open(path2, "r", encoding="utf-8") as f:
    code2 = f.read()

# Remove the python triggers
code2 = code2.replace("self.browser.page().runJavaScript('triggerWakeAnimation();')", "")
code2 = code2.replace("self.browser.loadFinished.connect(lambda ok: )", "") # just in case

with open(path2, "w", encoding="utf-8") as f:
    f.write(code2)

print("HTML onload trigger added!")
