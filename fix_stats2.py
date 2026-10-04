import re

path = r"D:\ultron\gui\index_v2.html"
with open(path, "r", encoding="utf-8") as f:
    html = f.read()

# Replace fake stats with real stats function
old_stats_regex = r"const cpu = Math\.floor\(Math\.random\(\) \* 15 \+ 8\);[\s\S]*?document\.getElementById\('gpu-bar'\)\.style\.width\s*=\s*gpu \+ '%';"

new_stats = "// Real stats updated via python updateRealStats()"
html = re.sub(old_stats_regex, new_stats, html)

update_fn = """function updateRealStats(cpu, ram, gpu) {
    document.getElementById('cpu-val').textContent = cpu + '%';
    document.getElementById('cpu-bar').style.width  = cpu + '%';
    document.getElementById('ram-val').textContent = ram + '%';
    document.getElementById('ram-bar').style.width  = ram + '%';
    document.getElementById('gpu-val').textContent = gpu + '%';
    document.getElementById('gpu-bar').style.width  = gpu + '%';
}

function frame() {"""

html = html.replace("function frame() {", update_fn)

with open(path, "w", encoding="utf-8") as f:
    f.write(html)
print("Stats injected properly!")
