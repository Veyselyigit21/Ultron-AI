import re

def ts_to_js(filename, out_filename):
    with open(filename, 'r', encoding='utf-8') as f:
        code = f.read()

    if 'handTracker' in filename:
        code = re.sub(r'import\s*\{\s*FilesetResolver,\s*HandLandmarker.*?\}\s*from\s*"@mediapipe/tasks-vision";', 
                 "import { FilesetResolver, HandLandmarker } from 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.3/vision_bundle.js';", code, flags=re.DOTALL)
    
    if 'orbScene' in filename:
        # replace three.js imports
        code = re.sub(r'import \* as THREE from "three";', "import * as THREE from 'https://unpkg.com/three@0.160.0/build/three.module.js';", code)
        code = re.sub(r'import \{ OrbitControls \} from "three/addons/controls/OrbitControls\.js";', "import { OrbitControls } from 'https://unpkg.com/three@0.160.0/examples/jsm/controls/OrbitControls.js';", code)
        code = re.sub(r'import \{ EffectComposer \} from "three/addons/postprocessing/EffectComposer\.js";', "import { EffectComposer } from 'https://unpkg.com/three@0.160.0/examples/jsm/postprocessing/EffectComposer.js';", code)
        code = re.sub(r'import \{ RenderPass \} from "three/addons/postprocessing/RenderPass\.js";', "import { RenderPass } from 'https://unpkg.com/three@0.160.0/examples/jsm/postprocessing/RenderPass.js';", code)
        code = re.sub(r'import \{ UnrealBloomPass \} from "three/addons/postprocessing/UnrealBloomPass\.js";', "import { UnrealBloomPass } from 'https://unpkg.com/three@0.160.0/examples/jsm/postprocessing/UnrealBloomPass.js';", code)
        code = re.sub(r'import \{ ShaderPass \} from "three/addons/postprocessing/ShaderPass\.js";', "import { ShaderPass } from 'https://unpkg.com/three@0.160.0/examples/jsm/postprocessing/ShaderPass.js';", code)

    # Remove export interfaces and types
    code = re.sub(r'(?m)^export interface \w+ \{.*?^\}', '', code, flags=re.DOTALL|re.MULTILINE)
    code = re.sub(r'(?m)^interface \w+ \{.*?^\}', '', code, flags=re.DOTALL|re.MULTILINE)
    code = re.sub(r'(?m)^export type \w+ = .*?;', '', code)

    # Remove basic types
    code = code.replace(' as const', '')
    code = code.replace(' | null', '')
    code = re.sub(r' satisfies \w+', '', code)
    code = re.sub(r' as \w+', '', code)
    
    # Remove simple variable types like let x: number = 5 -> let x = 5
    # We will do this carefully for function arguments.
    # Like unction foo(x: number, y: string) -> unction foo(x, y)
    code = re.sub(r'(\w+):\s*number', r'\1', code)
    code = re.sub(r'(\w+):\s*string', r'\1', code)
    code = re.sub(r'(\w+):\s*boolean', r'\1', code)
    code = re.sub(r'(\w+):\s*void', r'\1', code)
    code = re.sub(r'(\w+):\s*any', r'\1', code)
    code = re.sub(r'(\w+):\s*HTMLElement', r'\1', code)
    code = re.sub(r'(\w+):\s*HTMLVideoElement', r'\1', code)
    code = re.sub(r'(\w+):\s*HTMLCanvasElement', r'\1', code)
    code = re.sub(r'(\w+):\s*HandTrackerCallbacks', r'\1', code)
    code = re.sub(r'(\w+):\s*THREE\.Vector3\[\]', r'\1', code)
    code = re.sub(r'(\w+):\s*NormalizedLandmark\[\]\[\]', r'\1', code)
    code = re.sub(r'(\w+):\s*NormalizedLandmark', r'\1', code)
    code = re.sub(r'(\w+):\s*Point', r'\1', code)
    code = re.sub(r'(\w+):\s*TrackerStatus', r'\1', code)
    code = re.sub(r'(\w+):\s*GestureMode', r'\1', code)
    code = re.sub(r'(\w+):\s*string\[\]', r'\1', code)
    
    code = code.replace(': Promise<void>', '')
    code = code.replace(': void', '')
    code = re.sub(r'<string,\s*HandState>', '', code)
    code = re.sub(r'<string>', '', code)
    
    code = re.sub(r'private ', '', code)

    with open(out_filename, 'w', encoding='utf-8') as f:
        f.write(code)

ts_to_js('handTracker.ts', 'gui/assets/handTracker.js')
ts_to_js('orbScene.ts', 'gui/assets/orb.js')
