path = r"D:\ultron\gui\index_v2.html"
with open(path, "r", encoding="utf-8") as f:
    html = f.read()

# Fix scope
old_scope = """    let lastFrameTime = 0;
    let startupProgress = 1.0;
    let isStartingUp = false;"""

new_scope = """    let lastFrameTime = 0;
    window.startupProgress = 1.0;
    window.isStartingUp = false;"""

html = html.replace(old_scope, new_scope)

old_check = """if (isStartingUp) {"""
new_check = """if (window.isStartingUp) {"""
html = html.replace(old_check, new_check)

html = html.replace("startupProgress +=", "window.startupProgress +=")
html = html.replace("if (startupProgress >=", "if (window.startupProgress >=")
html = html.replace("startupProgress = 1.0", "window.startupProgress = 1.0")
html = html.replace("isStartingUp = false", "window.isStartingUp = false")
html = html.replace("ease(startupProgress)", "ease(window.startupProgress)")

old_trigger = """    startupProgress = 0.0;
    isStartingUp = true;"""
new_trigger = """    window.startupProgress = 0.0;
    window.isStartingUp = true;"""
html = html.replace(old_trigger, new_trigger)

# Re-add opacity 0 so it fades in
html = html.replace("opacity: 1;", "opacity: 0;")
html = html.replace("transform: scale(1);", "transform: scale(0.9);")

with open(path, "w", encoding="utf-8") as f:
    f.write(html)
print("Scope fixed!")
