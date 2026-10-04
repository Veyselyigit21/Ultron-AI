path = r"D:\ultron\gui\index.html"
with open(path, "r", encoding="utf-8-sig") as f:
    html = f.read()

# Replace triggerWakeAnimation
old_trigger = """function triggerWakeAnimation() {
    startupProgress = 0.0;
    isStartingUp = true;
    const cp = document.querySelector('.center-panel');
    if(cp) {
        cp.style.animation = 'none';
        cp.offsetHeight;
        cp.style.animation = 'startupGlow 1.0s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards';
    }
}"""
new_trigger = """function triggerWakeAnimation() {
    startupProgress = 0.0;
    isStartingUp = true;
    
    // Ekrani tamamen animasyona sok (Sag, sol paneller ve chat)
    const elements = document.querySelectorAll('.panel, .chat-container');
    elements.forEach(el => {
        el.style.animation = 'none';
        el.offsetHeight;
        el.style.animation = 'startupGlow 1.2s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards';
    });
}"""
html = html.replace(old_trigger, new_trigger)

# Ensure panels are hidden initially before animation
old_css_panel = """.panel {
    background: rgba(0, 10, 20, 0.5);"""
new_css_panel = """.panel {
    background: rgba(0, 10, 20, 0.5);
    opacity: 0;
    transform: scale(0.9);"""
if "transform: scale(0.9);" not in html:
    html = html.replace(old_css_panel, new_css_panel)
    
old_css_chat = """.chat-container {
    display:flex; flex-direction:column; gap:10px;"""
new_css_chat = """.chat-container {
    display:flex; flex-direction:column; gap:10px;
    opacity: 0;
    transform: scale(0.9);"""
if "opacity: 0;\n    transform: scale(0.9);" not in html:
    html = html.replace(old_css_chat, new_css_chat)

with open(path, "w", encoding="utf-8-sig") as f:
    f.write(html)
print("Tum paneller acilis animasyonuna eklendi!")
