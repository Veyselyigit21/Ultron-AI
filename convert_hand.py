import re

with open('handTracker.ts', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace imports
content = re.sub(r'import\s*\{\s*FilesetResolver,\s*HandLandmarker.*?\}\s*from\s*"@mediapipe/tasks-vision";', 
                 "import { FilesetResolver, HandLandmarker } from 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.3/vision_bundle.js';", content, flags=re.DOTALL)

# Strip out interfaces and type aliases
content = re.sub(r'export type \w+ = .*?;', '', content)
content = re.sub(r'(export )?interface \w+\s*\{.*?\}', '', content, flags=re.DOTALL)

# Strip out type annotations
content = re.sub(r':\s*[A-Z][A-Za-z0-9_]*(\[\])*', '', content)
content = re.sub(r':\s*(number|string|boolean|any|void)( |\[\]|;|,|\))', r'\2', content)

# Specific strip
content = re.sub(r'as const', '', content)
content = re.sub(r'private ', '', content)
content = re.sub(r'<string,\s*HandState>', '', content)
content = re.sub(r':\s*Point\s*\|\s*null', '', content)
content = re.sub(r':\s*number\s*\|\s*null', '', content)
content = re.sub(r'Promise<void>', '', content)

with open('gui/assets/handTracker.js', 'w', encoding='utf-8') as f:
    f.write(content)

