import re

with open('orbScene.ts', 'r', encoding='utf-8') as f:
    code = f.read()

# Replace three.js imports
code = re.sub(r'import \* as THREE from "three";', "import * as THREE from 'https://unpkg.com/three@0.160.0/build/three.module.js';", code)
code = re.sub(r'import \{ OrbitControls \} from "three/addons/controls/OrbitControls\.js";', "import { OrbitControls } from 'https://unpkg.com/three@0.160.0/examples/jsm/controls/OrbitControls.js';", code)
code = re.sub(r'import \{ EffectComposer \} from "three/addons/postprocessing/EffectComposer\.js";', "import { EffectComposer } from 'https://unpkg.com/three@0.160.0/examples/jsm/postprocessing/EffectComposer.js';", code)
code = re.sub(r'import \{ RenderPass \} from "three/addons/postprocessing/RenderPass\.js";', "import { RenderPass } from 'https://unpkg.com/three@0.160.0/examples/jsm/postprocessing/RenderPass.js';", code)
code = re.sub(r'import \{ UnrealBloomPass \} from "three/addons/postprocessing/UnrealBloomPass\.js";', "import { UnrealBloomPass } from 'https://unpkg.com/three@0.160.0/examples/jsm/postprocessing/UnrealBloomPass.js';", code)
code = re.sub(r'import \{ ShaderPass \} from "three/addons/postprocessing/ShaderPass\.js";', "import { ShaderPass } from 'https://unpkg.com/three@0.160.0/examples/jsm/postprocessing/ShaderPass.js';", code)

# Remove interfaces
code = re.sub(r'export interface OrbSceneApi \{.*?^\}', '', code, flags=re.DOTALL|re.MULTILINE)
code = re.sub(r'interface SpriteDrift \{.*?^\}', '', code, flags=re.DOTALL|re.MULTILINE)
code = re.sub(r'interface DebrisOrbit \{.*?^\}', '', code, flags=re.DOTALL|re.MULTILINE)

# Remove type annotations
code = code.replace('export function createOrbScene(container: HTMLElement): OrbSceneApi {', 'export function createOrbScene(container) {')
code = code.replace('function lineMat(color: number, opacity = 1) {', 'function lineMat(color, opacity = 1) {')
code = code.replace('function latRing(radius: number, lat: number, segs = 120) {', 'function latRing(radius, lat, segs = 120) {')
code = code.replace('function meridian(radius: number, lon: number, segs = 120) {', 'function meridian(radius, lon, segs = 120) {')
code = code.replace('const pts: THREE.Vector3[] = [];', 'const pts = [];')
code = code.replace('''function createSpherePanel(
    latCenter: number,
    lonCenter: number,
    latSpan: number,
    lonSpan: number,
    radius: number,
    divisions = 4,
  ) {''', '''function createSpherePanel(
    latCenter,
    lonCenter,
    latSpan,
    lonSpan,
    radius,
    divisions = 4,
  ) {''')
code = code.replace('function makeTextSprite(text: string, size = 0.08) {', 'function makeTextSprite(text, size = 0.08) {')
code = code.replace('function scatterText(count: number, sizeFn: () => number, rFn: () => number, speedScale: [number, number]) {', 'function scatterText(count, sizeFn, rFn, speedScale) {')
code = code.replace('} satisfies SpriteDrift;', '};')
code = code.replace('} satisfies DebrisOrbit;', '};')
code = code.replace('const u = d.userData as DebrisOrbit;', 'const u = d.userData;')
code = code.replace('const u = sp.userData as SpriteDrift;', 'const u = sp.userData;')
code = code.replace('function rotateBy(deltaTheta: number, deltaPhi: number) {', 'function rotateBy(deltaTheta, deltaPhi) {')
code = code.replace('function zoomBy(factor: number) {', 'function zoomBy(factor) {')
code = code.replace('function makeScanRing(radius: number, thickness = 0.015) {', 'function makeScanRing(radius, thickness = 0.015) {')

with open('gui/assets/orb.js', 'w', encoding='utf-8') as f:
    f.write(code)

with open('handTracker.ts', 'r', encoding='utf-8') as f:
    ht_code = f.read()

ht_code = re.sub(r'import\s*\{\s*FilesetResolver,\s*HandLandmarker.*?\}\s*from\s*"@mediapipe/tasks-vision";', 
                 "import { FilesetResolver, HandLandmarker } from 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.3/vision_bundle.js';", ht_code, flags=re.DOTALL)

ht_code = re.sub(r'export type GestureMode = "idle" \| "spin" \| "zoom";', '', ht_code)
ht_code = re.sub(r'export interface TrackerStatus \{.*?^\}', '', ht_code, flags=re.DOTALL|re.MULTILINE)
ht_code = re.sub(r'export interface HandTrackerCallbacks \{.*?^\}', '', ht_code, flags=re.DOTALL|re.MULTILINE)
ht_code = re.sub(r'interface Point \{.*?^\}', '', ht_code, flags=re.DOTALL|re.MULTILINE)
ht_code = re.sub(r'interface HandState \{.*?^\}', '', ht_code, flags=re.DOTALL|re.MULTILINE)

ht_code = ht_code.replace('private video: HTMLVideoElement;', 'video;')
ht_code = ht_code.replace('private overlay: HTMLCanvasElement;', 'overlay;')
ht_code = ht_code.replace('private callbacks: HandTrackerCallbacks;', 'callbacks;')
ht_code = ht_code.replace('private landmarker: HandLandmarker | null = null;', 'landmarker = null;')
ht_code = ht_code.replace('private stream: MediaStream | null = null;', 'stream = null;')
ht_code = ht_code.replace('private rafId = 0;', 'rafId = 0;')
ht_code = ht_code.replace('private running = false;', 'running = false;')
ht_code = ht_code.replace('private lastVideoTime = -1;', 'lastVideoTime = -1;')

ht_code = ht_code.replace('private handStates = new Map<string, HandState>();', 'handStates = new Map();')
ht_code = ht_code.replace('private prevMode: GestureMode = "idle";', 'prevMode = "idle";')
ht_code = ht_code.replace('private prevSpinGrab: Point | null = null;', 'prevSpinGrab = null;')
ht_code = ht_code.replace('private prevZoomDist: number | null = null;', 'prevZoomDist = null;')
ht_code = ht_code.replace('private lastStatus: TrackerStatus = { hands: 0, mode: "idle" };', 'lastStatus = { hands: 0, mode: "idle" };')

ht_code = ht_code.replace('''  constructor(
    video: HTMLVideoElement,
    overlay: HTMLCanvasElement,
    callbacks: HandTrackerCallbacks,
  ) {''', '''  constructor(
    video,
    overlay,
    callbacks,
  ) {''')

ht_code = ht_code.replace('async start(): Promise<void> {', 'async start() {')
ht_code = ht_code.replace('delegate: "GPU" as const', 'delegate: "GPU"')
ht_code = ht_code.replace('runningMode: "VIDEO" as const', 'runningMode: "VIDEO"')
ht_code = ht_code.replace('delegate: "CPU" as const', 'delegate: "CPU"')
ht_code = ht_code.replace('stop(): void {', 'stop() {')
ht_code = ht_code.replace('private loop = () => {', 'loop = () => {')

ht_code = ht_code.replace('''  private processHands(
    landmarks: NormalizedLandmark[][],
    labels: string[],
  ): void {''', '''  processHands(
    landmarks,
    labels,
  ) {''')

ht_code = ht_code.replace('const pinchedGrabs: Point[] = [];', 'const pinchedGrabs = [];')
ht_code = ht_code.replace('const seen = new Set<string>();', 'const seen = new Set();')
ht_code = ht_code.replace('const raw: Point = {', 'const raw = {')

ht_code = ht_code.replace('const mode: GestureMode =', 'const mode =')

ht_code = ht_code.replace('private emitStatus(status: TrackerStatus): void {', 'emitStatus(status) {')
ht_code = ht_code.replace('private drawOverlay(landmarks: NormalizedLandmark[][]): void {', 'drawOverlay(landmarks) {')

ht_code = ht_code.replace('function dist2d(a: NormalizedLandmark, b: NormalizedLandmark): number {', 'function dist2d(a, b) {')

with open('gui/assets/handTracker.js', 'w', encoding='utf-8') as f:
    f.write(ht_code)

