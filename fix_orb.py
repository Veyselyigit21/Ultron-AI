import re

with open('gui/assets/orb.js', 'r', encoding='utf-8') as f:
    code = f.read()

# Fix (scanRing1.material as THREE.MeshBasicMaterial).opacity
code = re.sub(r' as [A-Za-z0-9_\.]+', '', code)

with open('gui/assets/orb.js', 'w', encoding='utf-8') as f:
    f.write(code)

