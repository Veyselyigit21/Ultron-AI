path = r"D:\ultron\senses\background_ear.py"
with open(path, "r", encoding="utf-8") as f:
    code = f.read()

import re
code = re.sub(r"try:\s*import winsound\s*winsound\.PlaySound.*?\s*except:\s*pass", "", code, flags=re.DOTALL)

with open(path, "w", encoding="utf-8") as f:
    f.write(code)

path2 = r"D:\ultron\gui\index_v2.html"
with open(path2, "r", encoding="utf-8") as f:
    html = f.read()

old_trigger = """function triggerWakeAnimation() {"""
new_trigger = """let hasAnimated = false;
function triggerWakeAnimation() {
    if (hasAnimated) return;
    hasAnimated = true;"""
if "let hasAnimated = false;" not in html:
    html = html.replace(old_trigger, new_trigger)

with open(path2, "w", encoding="utf-8") as f:
    f.write(html)
print("Multiple triggers fixed!")
