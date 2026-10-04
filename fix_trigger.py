import re

path = r"D:\ultron\gui\index_v2.html"
with open(path, "r", encoding="utf-8") as f:
    html = f.read()

old_trigger_regex = r"function triggerWakeAnimation\(\)\s*\{[\s\S]*?\}\n\n"

new_trigger = """function triggerWakeAnimation() {
    startupProgress = 0.0;
    isStartingUp = true;
    
    const elements = document.querySelectorAll('.panel, .chat-section');
    elements.forEach(el => {
        el.style.animation = 'none';
        el.offsetHeight;
        el.style.animation = 'startupGlow 1.2s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards';
    });
}

"""

html = re.sub(old_trigger_regex, new_trigger, html, count=1)

with open(path, "w", encoding="utf-8") as f:
    f.write(html)
print("triggerWakeAnimation completely rewritten!")
