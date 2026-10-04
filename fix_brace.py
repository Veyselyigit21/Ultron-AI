path = r"D:\ultron\gui\index_v2.html"
with open(path, "r", encoding="utf-8") as f:
    html = f.read()

import re
html = re.sub(r"\}\n\n\}\n\n\n\nfunction receiveMessage", "}\n\n\n\nfunction receiveMessage", html)

with open(path, "w", encoding="utf-8") as f:
    f.write(html)
print("Extra brace removed!")
