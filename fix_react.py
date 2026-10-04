import os

path = r"D:\ultron\gui\index.html"
with open(path, "r", encoding="utf-8-sig") as f:
    html = f.read()

# Fix rawVol logic
old_vol = """        } else if (isVoiceActive) {
            rawVol = micVolume; // GERCEK SES
        } else {
            rawVol = 0;
        }"""
        
new_vol = """        } else {
            rawVol = micVolume; // Her zaman tepki ver
        }"""
html = html.replace(old_vol, new_vol)

with open(path, "w", encoding="utf-8-sig") as f:
    f.write(html)
print("Reaktor sesi fixlendi")
