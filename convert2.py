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

    # Remove interfaces (non-DOTALL for safe removal)
    text = re.sub(r'export interface OrbSceneApi \{[\s\S]*?\}', '', text)
    text = re.sub(r'interface SpriteDrift \{[\s\S]*?\}', '', text)
    text = re.sub(r'interface DebrisOrbit \{[\s\S]*?\}', '', text)

    # Return type of createOrbScene
    text = text.replace('export function createOrbScene(container: HTMLElement): OrbSceneApi {', 'export function createOrbScene(container) {')
    text = text.replace('export function createOrbScene(container: HTMLElement) {', 'export function createOrbScene(container) {')
    
    # Types
    text = text.replace('deltaTheta: number, deltaPhi: number', 'deltaTheta, deltaPhi')
    text = text.replace('factor: number', 'factor')
    text = text.replace('color: number', 'color')
    text = text.replace('radius: number, lat: number, segs = 120', 'radius, lat, segs = 120')
    text = text.replace('radius: number, lon: number, segs = 120', 'radius, lon, segs = 120')
    text = text.replace('latCenter: number,\n    lonCenter: number,\n    latSpan: number,\n    lonSpan: number,\n    radius: number,\n    divisions = 4,', 'latCenter,\n    lonCenter,\n    latSpan,\n    lonSpan,\n    radius,\n    divisions = 4,')
    text = text.replace('text: string, size = 0.08', 'text, size = 0.08')
    text = text.replace('count: number, sizeFn: () => number, rFn: () => number, speedScale: [number, number]', 'count, sizeFn, rFn, speedScale')
    text = text.replace('radius: number, thickness = 0.015', 'radius, thickness = 0.015')

    text = text.replace('const pts: THREE.Vector3[] = [];', 'const pts = [];')
    text = text.replace('const trailPts: THREE.Vector3[] = [];', 'const trailPts = [];')
    text = text.replace('const debris: THREE.Mesh[] = [];', 'const debris = [];')
    text = text.replace('const driftGroups: [THREE.Group, number][] = [', 'const driftGroups = [')

    text = text.replace(' satisfies SpriteDrift', '')
    text = text.replace(' satisfies DebrisOrbit', '')
    text = text.replace(' as DebrisOrbit', '')
    text = text.replace(' as SpriteDrift', '')

    with open(r'D:\ultron\gui\assets\orb.js', 'w', encoding='utf-8') as f:
        f.write(text)

convert_orb()
