path = r"D:\ultron\gui\index_v2.html"
with open(path, "r", encoding="utf-8") as f:
    html = f.read()

old_glow = """@keyframes startupGlow {
    0%   { box-shadow: 0 0 0 rgba(0, 180, 255, 0); border-color: rgba(0, 180, 255, 0.1); }
    50%  { box-shadow: 0 0 40px rgba(0, 180, 255, 0.4); border-color: rgba(0, 180, 255, 0.6); }
    100% { box-shadow: 0 0 10px rgba(0, 180, 255, 0.1); border-color: rgba(0, 180, 255, 0.2); }
}"""

new_glow = """@keyframes startupGlow {
    0%   { opacity: 0; transform: scale(0.9); box-shadow: 0 0 0 rgba(0, 180, 255, 0); border-color: rgba(0, 180, 255, 0.1); }
    50%  { opacity: 1; transform: scale(1.05); box-shadow: 0 0 40px rgba(0, 180, 255, 0.4); border-color: rgba(0, 180, 255, 0.6); }
    100% { opacity: 1; transform: scale(1.0); box-shadow: 0 0 10px rgba(0, 180, 255, 0.1); border-color: rgba(0, 180, 255, 0.2); }
}"""

html = html.replace(old_glow, new_glow)

with open(path, "w", encoding="utf-8") as f:
    f.write(html)
print("Keyframes fixed!")
