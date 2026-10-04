path = r"D:\ultron\gui\index_v2.html"
with open(path, "r", encoding="utf-8") as f:
    html = f.read()

html = html.replace("opacity: 0;", "opacity: 1;")
html = html.replace("transform: scale(0.9);", "transform: scale(1);")

with open(path, "w", encoding="utf-8") as f:
    f.write(html)
print("Opacity fixed to 1!")
