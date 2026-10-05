import re

def convert_orb():
    with open(r'D:\ultron\orbScene.ts', 'r', encoding='utf-8') as f:
        text = f.read()

    # Imports
    text = re.sub(
        r'import \* as THREE from "three";',
        r"import * as THREE from 'https://unpkg.com/three@0.160.0/build/three.module.js';",
        text
    )
    text = re.sub(
        r'import { ([^}]+) } from "three/addons/controls/([^"]+)";',
        r"import { \1 } from 'https://unpkg.com/three@0.160.0/examples/jsm/controls/\2';",
        text
    )
    text = re.sub(
        r'import { ([^}]+) } from "three/addons/postprocessing/([^"]+)";',
        r"import { \1 } from 'https://unpkg.com/three@0.160.0/examples/jsm/postprocessing/\2';",
        text
    )

    # Interfaces
    text = re.sub(r'export interface OrbSceneApi \{.*?\n\}\n', '', text, flags=re.DOTALL)
    text = re.sub(r'interface SpriteDrift \{.*?\n\}\n', '', text, flags=re.DOTALL)
    text = re.sub(r'interface DebrisOrbit \{.*?\n\}\n', '', text, flags=re.DOTALL)

    # Type annotations in functions
    text = text.replace('container: HTMLElement', 'container')
    text = text.replace('deltaTheta: number, deltaPhi: number', 'deltaTheta, deltaPhi')
    text = text.replace('factor: number', 'factor')
    text = text.replace('color: number', 'color')
    text = text.replace('radius: number, lat: number, segs = 120', 'radius, lat, segs = 120')
    text = text.replace('radius: number, lon: number, segs = 120', 'radius, lon, segs = 120')
    text = text.replace('latCenter: number,\n    lonCenter: number,\n    latSpan: number,\n    lonSpan: number,\n    radius: number,\n    divisions = 4,', 'latCenter,\n    lonCenter,\n    latSpan,\n    lonSpan,\n    radius,\n    divisions = 4,')
    text = text.replace('text: string, size = 0.08', 'text, size = 0.08')
    text = text.replace('count: number, sizeFn: () => number, rFn: () => number, speedScale: [number, number]', 'count, sizeFn, rFn, speedScale')
    text = text.replace('radius: number, thickness = 0.015', 'radius, thickness = 0.015')

    # Type annotations in variables
    text = text.replace('const pts: THREE.Vector3[] = [];', 'const pts = [];')
    text = text.replace('const trailPts: THREE.Vector3[] = [];', 'const trailPts = [];')
    text = text.replace('const debris: THREE.Mesh[] = [];', 'const debris = [];')
    text = text.replace('const driftGroups: [THREE.Group, number][] = [', 'const driftGroups = [')

    # satisfies and as
    text = text.replace(' satisfies SpriteDrift', '')
    text = text.replace(' satisfies DebrisOrbit', '')
    text = text.replace(' as DebrisOrbit', '')
    text = text.replace(' as SpriteDrift', '')

    with open(r'D:\ultron\gui\assets\orb.js', 'w', encoding='utf-8') as f:
        f.write(text)

def convert_hand():
    with open(r'D:\ultron\handTracker.ts', 'r', encoding='utf-8') as f:
        text = f.read()

    # Imports
    text = re.sub(
        r'import \{[^}]+\} from "@mediapipe/tasks-vision";',
        r"import { FilesetResolver, HandLandmarker } from 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.3/vision_bundle.js';",
        text, flags=re.DOTALL
    )

    # Interfaces and types
    text = re.sub(r'export type GestureMode = "idle" | "spin" | "zoom";\n', '', text)
    text = re.sub(r'export interface TrackerStatus \{[^}]+\}\n', '', text, flags=re.DOTALL)
    text = re.sub(r'export interface HandTrackerCallbacks \{[^}]+\}\n', '', text, flags=re.DOTALL)
    text = re.sub(r'interface Point \{[^}]+\}\n', '', text, flags=re.DOTALL)
    text = re.sub(r'interface HandState \{[^}]+\}\n', '', text, flags=re.DOTALL)

    # Variable types
    text = re.sub(r': HTMLVideoElement', '', text)
    text = re.sub(r': HTMLCanvasElement', '', text)
    text = re.sub(r': HandTrackerCallbacks', '', text)
    text = re.sub(r': HandLandmarker \| null = null', ' = null', text)
    text = re.sub(r': MediaStream \| null = null', ' = null', text)
    text = re.sub(r': GestureMode = "idle"', ' = "idle"', text)
    text = re.sub(r': Point \| null = null', ' = null', text)
    text = re.sub(r': number \| null = null', ' = null', text)
    text = re.sub(r': TrackerStatus =', ' =', text)
    text = re.sub(r': HandState', '', text)
    text = re.sub(r'private handStates = new Map<string, HandState>\(\);', 'private handStates = new Map();', text)

    # Function types
    text = re.sub(r'async start\(\): Promise<void>', 'async start()', text)
    text = re.sub(r'stop\(\): void', 'stop()', text)
    text = re.sub(r'private processHands\([^)]+\): void', 'private processHands(landmarks, labels)', text)
    text = re.sub(r'private emitStatus\([^)]+\): void', 'private emitStatus(status)', text)
    text = re.sub(r'private drawOverlay\([^)]+\): void', 'private drawOverlay(landmarks)', text)
    text = re.sub(r'function dist2d\([^)]+\): number', 'function dist2d(a, b)', text)

    # 'as const'
    text = text.replace(' as const', '')
    
    # local variable types
    text = text.replace('const pinchedGrabs: Point[] = [];', 'const pinchedGrabs = [];')
    text = text.replace('const seen = new Set<string>();', 'const seen = new Set();')
    text = text.replace('const raw: Point = {', 'const raw = {')
    text = text.replace('const mode: GestureMode =', 'const mode =')

    with open(r'D:\ultron\gui\assets\handTracker.js', 'w', encoding='utf-8') as f:
        f.write(text)

convert_orb()
convert_hand()
