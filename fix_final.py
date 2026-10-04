import os
import re

html_path = r"D:\ultron\gui\index.html"
with open(html_path, "r", encoding="utf-8-sig") as f:
    html = f.read()

# 1. Reduce reactor size and add JS startup logic
# Add startup variables
if "let startupProgress = 1.0;" not in html:
    html = html.replace("let lastFrameTime = 0;", "let lastFrameTime = 0;\n    let startupProgress = 1.0;\n    let isStartingUp = false;")

# Modify triggerWakeAnimation
old_trigger = """function triggerWakeAnimation() {
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
    const cp = document.querySelector('.center-panel');
    if(cp) {
        cp.style.animation = 'none';
        cp.offsetHeight;
        cp.style.animation = 'startupGlow 1.0s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards';
    }
}"""
html = html.replace(old_trigger, new_trigger)

# Modify the animation frame for startup logic
old_rawVol = """        let rawVol = 0;"""
new_rawVol = """        if (isStartingUp) {
            startupProgress += 0.015; // Approx 1.0 sec animation
            if (startupProgress >= 1.0) {
                startupProgress = 1.0;
                isStartingUp = false;
            }
        }
        let rawVol = 0;"""
html = html.replace(old_rawVol, new_rawVol)

# Modify BASE and rings
old_base = """const BASE = Math.min(W, H) * 0.35;"""
new_base = """
        // Easing function for sick iron-man assembly effect
        const ease = (t) => t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
        const p = ease(startupProgress);
        const BASE = Math.min(W, H) * 0.22 * p; // Size reduced from 0.35 to 0.22 and multiplied by progress
"""
html = html.replace(old_base, new_base)

# Modify angles to include introSpin
old_ang1 = """const ang1 = t * 0.18;"""
old_ang2 = """const ang2 = -t * 0.28;"""
new_ang1 = """const introSpin = (1 - p) * Math.PI * 5;
        const ang1 = t * 0.18 + introSpin;"""
new_ang2 = """const ang2 = -t * 0.28 - introSpin;"""
html = html.replace(old_ang1, new_ang1)
html = html.replace(old_ang2, new_ang2)

# Text scaling
old_font = """ctx.font        = `bold ${Math.floor(BASE * 0.13 * S)}px "Courier New", Courier, monospace`;"""
new_font = """ctx.font        = `bold ${Math.floor(BASE * 0.15 * S * p)}px "Courier New", Courier, monospace`;"""
html = html.replace(old_font, new_font)
html = html.replace('ctx.fillStyle   = `rgba(100, 220, 255,${0.85+volume*0.15})`', 'ctx.fillStyle   = `rgba(100, 220, 255,${(0.85+volume*0.15)*p})`')

with open(html_path, "w", encoding="utf-8-sig") as f:
    f.write(html)
print("HTML animations added")

# 2. Fix main_gui.py flickering (Remove the GPU flags that cause tears)
py_path = r"D:\ultron\main_gui.py"
with open(py_path, "r", encoding="utf-8") as f:
    py = f.read()

py = py.replace('os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--enable-gpu-rasterization --ignore-gpu-blocklist"',
                '# Removed unstable GPU flags that cause flickering')
with open(py_path, "w", encoding="utf-8") as f:
    f.write(py)
print("Python flags fixed")
