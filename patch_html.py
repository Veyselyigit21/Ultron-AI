import re

html_path = r'D:\ultron\gui\index_v2.html'
with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Remove 2D Arc Reactor logic
start = html.find('// ULTRON / IRON MAN REAKTÖRÜ')
end = html.find('// ECG ANİMASYONU')
if start != -1 and end != -1:
    html = html[:start] + html[end:]

# 2. Add styles for the new UI
style_injection = """
/* ─ 3D ORB & HAND TRACKER UI ─ */
.camera-panel {
    position: absolute;
    top: 10px;
    right: 10px;
    width: 208px;
    display: flex;
    flex-direction: column;
    gap: 5px;
    z-index: 100;
}
.camera-video {
    display: none;
}
.camera-overlay {
    width: 208px;
    height: 156px;
    background: rgba(0,0,0,0.5);
    border: 1px solid rgba(0, 180, 255, 0.4);
    border-radius: 4px;
    transform: scaleX(-1);
}
.camera-status {
    font-size: 10px;
    color: #00c3ff;
    text-align: center;
    letter-spacing: 1px;
}
.hud-controls {
    position: absolute;
    bottom: 10px;
    left: 10px;
    display: flex;
    gap: 10px;
    z-index: 100;
}
.hud-btn {
    background: rgba(0, 0, 0, 0.6);
    border: 1px solid rgba(0, 180, 255, 0.4);
    color: #fff;
    padding: 5px 15px;
    font-family: 'Rajdhani', sans-serif;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    border-radius: 4px;
    transition: 0.3s;
}
.hud-btn:hover {
    background: rgba(0, 180, 255, 0.3);
}
</style>
"""
html = html.replace('</style>', style_injection)

# 3. Add HTML elements inside .orb-wrapper
orb_html = """
        <div class="orb-wrapper" style="position: relative;">
            <div class="camera-panel" id="camera-panel" style="display: none;">
                <video id="camera-video" muted playsInline class="camera-video"></video>
                <canvas id="camera-overlay" width="208" height="156" class="camera-overlay"></canvas>
                <div id="camera-status" class="camera-status">SHOW HANDS</div>
            </div>
            <div class="hud-controls">
                <button id="btn-toggle-gestures" class="hud-btn">GESTURES OFF</button>
                <button id="btn-zoom-in" class="hud-btn">+</button>
                <button id="btn-zoom-out" class="hud-btn">−</button>
                <button id="btn-reset" class="hud-btn">RESET</button>
            </div>
"""
html = re.sub(r'<div class="orb-wrapper">.*?</div>', orb_html + '        </div>', html, flags=re.DOTALL)

# 4. Inject script block at the end of body
script_injection = """
<script type="module">
  import { createOrbScene } from './assets/orb.js';
  import { HandTracker } from './assets/handTracker.js';

  const container = document.querySelector('.orb-wrapper');
  
  // Clean up any remaining canvases that might conflict
  const existingCanvas = document.getElementById('orb-canvas');
  if (existingCanvas) existingCanvas.remove();

  const scene = createOrbScene(container);
  
  const video = document.getElementById('camera-video');
  const overlay = document.getElementById('camera-overlay');
  const statusEl = document.getElementById('camera-status');
  const toggleBtn = document.getElementById('btn-toggle-gestures');
  const cameraPanel = document.getElementById('camera-panel');
  
  const MODE_LABEL = {
    idle: "STANDBY",
    spin: "SPIN",
    zoom: "ZOOM",
  };

  const tracker = new HandTracker(video, overlay, {
    onRotate: (dt, dp) => scene.rotateBy(dt, dp),
    onZoom: (factor) => scene.zoomBy(factor),
    onStatus: (status) => {
        if (status.hands > 0) {
            statusEl.textContent = `${status.hands} HAND${status.hands > 1 ? "S" : ""} · ${MODE_LABEL[status.mode]}`;
        } else {
            statusEl.textContent = "SHOW HANDS";
        }
    }
  });

  let cameraOn = false;
  let initializing = false;

  toggleBtn.addEventListener('click', async () => {
      if (initializing) return;
      if (cameraOn) {
          tracker.stop();
          cameraOn = false;
          toggleBtn.textContent = "GESTURES OFF";
          statusEl.textContent = "SHOW HANDS";
          cameraPanel.style.display = 'none';
      } else {
          initializing = true;
          toggleBtn.textContent = "INITIALIZING...";
          try {
              await tracker.start();
              cameraOn = true;
              toggleBtn.textContent = "GESTURES ON";
              cameraPanel.style.display = 'flex';
          } catch (e) {
              console.error(e);
              toggleBtn.textContent = "ERROR";
              setTimeout(() => toggleBtn.textContent = "GESTURES OFF", 2000);
          }
          initializing = false;
      }
  });

  document.getElementById('btn-zoom-in').addEventListener('click', () => scene.zoomIn());
  document.getElementById('btn-zoom-out').addEventListener('click', () => scene.zoomOut());
  document.getElementById('btn-reset').addEventListener('click', () => scene.resetView());

  window.addEventListener("keydown", (e) => {
      switch (e.key) {
        case "+":
        case "=":
          scene.zoomIn();
          break;
        case "-":
        case "_":
          scene.zoomOut();
          break;
        case "r":
        case "R":
          scene.resetView();
          break;
        case "g":
        case "G":
          toggleBtn.click();
          break;
      }
  });
</script>
</body>
"""
html = html.replace('</body>', script_injection)

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)
