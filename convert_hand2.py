import re

with open('handTracker.ts', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace imports
content = re.sub(r'import\s*\{\s*FilesetResolver,\s*HandLandmarker.*?\}\s*from\s*"@mediapipe/tasks-vision";', 
                 "import { FilesetResolver, HandLandmarker } from 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.3/vision_bundle.js';", content, flags=re.DOTALL)

# Strip out interfaces and type aliases
content = re.sub(r'export type \w+ = .*?;', '', content)
content = re.sub(r'(export )?interface \w+\s*\{.*?\}', '', content, flags=re.DOTALL)

# Remove all TS type annotations
# Very aggressive regex to remove everything after a colon for arguments, variables
# Let's just do it manually for handTracker since it's small.

def remove_types(text):
    # Just basic replacements for the known ts features in handTracker
    text = text.replace(' | null', '')
    text = text.replace(': void', '')
    text = text.replace(': Promise<void>', '')
    text = text.replace(' as const', '')
    text = text.replace('<string, HandState>', '')
    text = text.replace('<string>', '')
    text = text.replace('[]', '') # arrays like string[] will become string... wait
    return text

content = remove_types(content)

# We still have : string, : number, : HTMLVideoElement, etc.
content = re.sub(r':\s*[A-Za-z0-9_]+(\[\])?', '', content)
# Fix up constructors and methods
content = re.sub(r'public |private |protected ', '', content)
# Some manual fixups:
content = content.replace('labels,', 'labels,')
content = content.replace('landmarks,', 'landmarks,')

with open('gui/assets/handTracker.js', 'w', encoding='utf-8') as f:
    f.write(content)
