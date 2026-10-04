path = r"D:\ultron\gui\index_v2.html"
with open(path, "r", encoding="utf-8") as f:
    html = f.read()

# Fix .panel CSS
import re
html = re.sub(r"\.panel\s*\{[^}]*\}", ".panel {\n    background: rgba(12, 4, 0, 0.85);\n    border: 1px solid rgba(0, 180, 255, 0.1);\n    border-radius: 10px;\n    padding: 20px;\n    display: flex;\n    flex-direction: column;\n    gap: 15px;\n    opacity: 0;\n    transform: scale(0.9);\n}", html)

# Fix .chat-section CSS
html = re.sub(r"\.chat-section\s*\{[^}]*\}", ".chat-section {\n    background: rgba(12, 4, 0, 0.85);\n    border-top: 1px solid rgba(0, 180, 255, 0.2);\n    padding: 15px 30px;\n    display: flex;\n    flex-direction: column;\n    gap: 10px;\n    position: relative;\n    opacity: 0;\n    transform: scale(0.9);\n}", html)

# Fix triggerWakeAnimation JS
old_js = """    // Ekrani tamamen animasyona sok (Sag, sol paneller ve chat)
    const elements = document.querySelectorAll('.panel, .chat-container');"""
new_js = """    // Ekrani tamamen animasyona sok (Sag, sol paneller ve chat)
    const elements = document.querySelectorAll('.panel, .chat-section');"""
html = html.replace(old_js, new_js)

with open(path, "w", encoding="utf-8") as f:
    f.write(html)
print("CSS and JS fixed for full animation!")
