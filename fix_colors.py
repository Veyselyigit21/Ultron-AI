import re

path = r"D:\ultron\gui\index.html"
with open(path, "r", encoding="utf-8-sig") as f:
    html = f.read()

# Change ECG line color to red
html = html.replace("ctx.strokeStyle = '#00c3ff';", "ctx.strokeStyle = 'rgba(255,20,50,1)';")

# Change orange text fill to cyan
html = re.sub(r'ctx\.fillStyle\s*=\s*`rgba\(255,\$\{200\s*\+\s*Math\.floor\(volume\*55\)\},\$\{80\+Math\.floor\(volume\*40\)\},\$\{0\.85\+volume\*0\.15\}\)`',
              'ctx.fillStyle = `rgba(100, 220, 255,${0.85+volume*0.15})`', html)

# Change orange rings around text to cyan
html = re.sub(r'ctx\.strokeStyle\s*=\s*`rgba\(255,\$\{100\+i\*25\},0,\$\{wa\}\)`',
              'ctx.strokeStyle = `rgba(0, 180, 255,${wa})`', html)

# Make sure we didn't miss any other orange hardcodes
html = html.replace("rgba(255,${100+i*25},0,${wa})", "rgba(0,180,255,${wa})")

with open(path, "w", encoding="utf-8-sig") as f:
    f.write(html)
print("Renkler guncellendi")
