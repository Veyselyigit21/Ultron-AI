"""ULTRON — ana uygulama (tek süreç: arayüz + kulak + ağız + beyin).

Çalıştır:  python main_gui.py         (pencere açık başlar)
           pythonw main_gui.py --hidden   (sadece tray'de başlar; "Ultron" diyince açılır)
Kısayol:   Ctrl+Alt+U ile de uyandırılabilir.
"""
from __future__ import annotations

import json
import os
import random
import sys
import threading
import time
from datetime import datetime

from PyQt6.QtCore import QObject, Qt, QTimer, QUrl, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QAction, QBrush, QColor, QIcon, QPainter, QPixmap
from PyQt6.QtNetwork import QLocalServer, QLocalSocket
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtWebEngineCore import QWebEnginePage
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QApplication, QMainWindow, QMenu, QSystemTrayIcon

from core.config import ASSETS_DIR, GUI_FILE, get_logger, settings
from core.llm_manager import LLMManager
from senses.background_ear import BackgroundEar
from senses.voice import Mouth

log = get_logger("ultron.gui")
INSTANCE_KEY = "ultron_ai_single_instance_v3"


def _excepthook(t, v, tb):
    log.error("Yakalanmamış hata", exc_info=(t, v, tb))


sys.excepthook = _excepthook
threading.excepthook = lambda a: log.error("Thread hatası", exc_info=(a.exc_type, a.exc_value, a.exc_traceback))


def make_icon() -> QIcon:
    pm = QPixmap(64, 64)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor(0, 180, 255)))
    p.drawEllipse(6, 6, 52, 52)
    p.setBrush(QBrush(QColor(3, 1, 0)))
    p.drawEllipse(22, 22, 20, 20)
    p.end()
    return QIcon(pm)


class JsLogPage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, line, source):
        log.info("JS[%s] %s (satır %s)", level.name if hasattr(level, "name") else level, message, line)


class Bridge(QObject):
    """JS'in çağırabildiği TEK yüzey."""

    def __init__(self, backend: "Backend"):
        super().__init__()
        self._b = backend

    @pyqtSlot(str)
    def processInput(self, text: str) -> None:
        self._b.process_input(text)


class Backend(QObject):
    run_js = pyqtSignal(str)
    show_ui = pyqtSignal()
    hide_ui = pyqtSignal()
    quit_app = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.mouth = Mouth(on_state=self._on_speaking)
        self.llm = LLMManager(on_event=self._on_event)
        self.ear = BackgroundEar(on_wake=self._on_wake, on_command=self._on_command, on_level=self._on_level,
                                 on_state=lambda s: self.js("setListenState", s), on_error=self._on_error,
                                 mouth=self.mouth)
        self._last_level = 0.0

    # ───────── JS köprüsü ─────────
    def js(self, fn: str, *args) -> None:
        a = ",".join(json.dumps(x, ensure_ascii=False) for x in args)
        self.run_js.emit(f"if(typeof {fn}==='function'){{{fn}({a});}}")

    def say(self, text: str, speak: bool = True) -> None:
        self.js("receiveMessage", text)
        if speak:
            self.mouth.speak(text)

    # ───────── kulaktan gelenler ─────────
    def _on_level(self, rms: float) -> None:
        now = time.time()
        if now - self._last_level > 0.066:
            self._last_level = now
            self.js("setMicLevel", rms / 1000.0)

    def _on_wake(self) -> None:
        self.show_ui.emit()
        self.js("triggerWakeAnimation", True)
        try:
            import winsound
            winsound.PlaySound(str(ASSETS_DIR / "wake_cyber.wav"), winsound.SND_FILENAME | winsound.SND_ASYNC)
        except Exception:
            pass

    def _on_command(self, text: str) -> None:
        self.show_ui.emit()
        self.js("receiveVoiceInput", text)
        threading.Thread(target=self._ask, args=(text,), daemon=True).start()

    def _on_error(self, msg: str) -> None:
        log.warning(msg)
        self.js("systemMessage", msg)

    # ───────── konuşma durumu ─────────
    def _on_speaking(self, speaking: bool) -> None:
        self.js("setSpeaking", speaking)
        if not speaking:
            self.ear.extend_conversation()

    # ───────── yazılı/sesli giriş ─────────
    def process_input(self, text: str) -> None:
        text = (text or "").strip()
        if text:
            self.mouth.interrupt()
            threading.Thread(target=self._ask, args=(text,), daemon=True).start()

    def _ask(self, text: str) -> None:
        self.js("setThinking", True)
        reply = self.llm.ask(text)
        self.js("setThinking", False)
        if reply.display:
            self.js("receiveMessage", reply.display)
        if reply.speech:
            self.mouth.speak(reply.speech)
        else:
            self.ear.extend_conversation()
        self._sync_confirm()
        self._sync_model()

    def _sync_confirm(self) -> None:
        p = self.llm.pending
        self.js("showConfirm", p[0]) if p else self.js("hideConfirm")

    def _sync_model(self) -> None:
        mode, act = settings["mode"], self.llm.active_backend
        if mode == "offline" or (mode == "auto" and act == "offline"):
            label = "Ollama [OFFLINE]"
        else:
            label = f"{settings['online_model'].split('/')[-1]} [ONLINE]"
        self.js("setModelLabel", label + (" · AUTO" if mode == "auto" else ""))

    # ───────── beyinden gelen olaylar ─────────
    def _on_event(self, name: str, payload=None) -> None:
        if name == "hide":
            self.hide_ui.emit()
        elif name == "quit":
            def bye():
                self.mouth.wait_done(8)
                self.quit_app.emit()
            threading.Thread(target=bye, daemon=True).start()
        elif name == "stop_speaking":
            self.mouth.interrupt()
        elif name == "notify":
            self.say(str(payload))
            self._sync_confirm()
        elif name in ("mode", "backend"):
            self._sync_model()
        elif name == "authority":
            self.js("setAuthority", int(payload or 0))

    def greet(self) -> None:
        h = datetime.now().hour
        part = ("Gece mesaisi mi patron?" if h < 5 else "Günaydın patron." if h < 12 else "İyi günler patron."
                if h < 18 else "İyi akşamlar patron.")
        extra = random.choice(["Tüm protokoller devrede.", "Sistemler aktif, dinliyorum.", "Çekirdek çevrimiçi."])
        self.say(f"{part} {extra} Saat {datetime.now():%H:%M}.")
        self._sync_model()


class UltronWindow(QMainWindow):
    def __init__(self, backend: Backend, start_hidden: bool):
        super().__init__()
        self.backend = backend
        self._really_quit = False
        self._ready = False
        self._queue: list[str] = []
        self.setWindowTitle("ULTRON")
        self.setWindowIcon(make_icon())
        self.setStyleSheet("background-color:#050505;")

        self.view = QWebEngineView()
        self.view.setPage(JsLogPage(self.view))
        self.view.page().setBackgroundColor(Qt.GlobalColor.black)
        self.channel = QWebChannel()
        self.bridge = Bridge(backend)
        self.channel.registerObject("backend", self.bridge)
        self.view.page().setWebChannel(self.channel)
        self.view.loadFinished.connect(self._loaded)
        self.setCentralWidget(self.view)

        backend.run_js.connect(self._run_js)
        backend.show_ui.connect(self.bring_front)
        backend.hide_ui.connect(self.hide)
        backend.quit_app.connect(self.quit)

        self._setup_tray()
        self.view.setUrl(QUrl.fromLocalFile(str(GUI_FILE)))
        if not start_hidden:
            self.showMaximized()

        self.stats_timer = QTimer(self)
        self.stats_timer.timeout.connect(self._stats)
        self.stats_timer.start(2000)

    # ───────── JS ─────────
    def _run_js(self, code: str) -> None:
        if self._ready:
            self.view.page().runJavaScript(code)
        else:
            self._queue.append(code)

    def _loaded(self, ok: bool) -> None:
        if not ok:
            log.error("Arayüz yüklenemedi: %s", GUI_FILE)
            return
        self._ready = True
        for c in self._queue:
            self.view.page().runJavaScript(c)
        self._queue.clear()
        self.backend.ear.start()
        threading.Thread(target=self.backend.greet, daemon=True).start()

    def _stats(self) -> None:
        try:
            import psutil
            self._run_js(f"if(typeof updateRealStats==='function')updateRealStats({int(psutil.cpu_percent())},"
                         f"{int(psutil.virtual_memory().percent)},-1);")
        except Exception:
            pass

    # ───────── pencere/tray ─────────
    def bring_front(self) -> None:
        if self.isMinimized():
            self.showNormal()
        self.showMaximized()
        self.raise_()
        self.activateWindow()

    def _setup_tray(self) -> None:
        self.tray = QSystemTrayIcon(make_icon(), self)
        self.tray.setToolTip("ULTRON")
        m = QMenu()
        m.addAction("Arayüzü göster", self.bring_front)
        m.addAction("Arayüzü gizle", self.hide)
        m.addSeparator()
        mode = m.addMenu("Mod")
        for label, val in (("Otomatik", "auto"), ("Online", "online"), ("Offline", "offline")):
            mode.addAction(label, lambda v=val: self.backend.llm._set_mode(v))
        m.addAction("Tam yetki 30 dk", lambda: self.backend.say(self.backend.llm._authority("ac 30")))
        m.addAction("Tam yetkiyi kapat", lambda: self.backend.say(self.backend.llm._authority("kapat")))
        pause = QAction("Dinlemeyi duraklat", m, checkable=True)
        pause.toggled.connect(lambda c: self.backend.ear.pause() if c else self.backend.ear.resume())
        m.addAction(pause)
        m.addSeparator()
        m.addAction("Çıkış", self.quit)
        self.tray.setContextMenu(m)
        self.tray.activated.connect(lambda r: self.bring_front()
                                    if r in (QSystemTrayIcon.ActivationReason.Trigger,
                                             QSystemTrayIcon.ActivationReason.DoubleClick) else None)
        self.tray.show()

    def closeEvent(self, e) -> None:
        if self._really_quit:
            e.accept()
        else:
            e.ignore()
            self.hide()  # X'e basınca kapanmaz, tray'e iner

    def quit(self) -> None:
        self._really_quit = True
        self.backend.ear.stop()
        self.backend.mouth.interrupt()
        self.tray.hide()
        QApplication.quit()
        threading.Timer(2.0, lambda: os._exit(0)).start()


def already_running() -> bool:
    s = QLocalSocket()
    s.connectToServer(INSTANCE_KEY)
    if s.waitForConnected(300):
        s.write(b"show")
        s.flush()
        s.waitForBytesWritten(300)
        s.disconnectFromServer()
        return True
    return False


def main() -> int:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    if already_running():
        return 0
    server = QLocalServer()
    QLocalServer.removeServer(INSTANCE_KEY)
    server.listen(INSTANCE_KEY)

    backend = Backend()
    win = UltronWindow(backend, start_hidden="--hidden" in sys.argv)
    server.newConnection.connect(lambda: (server.nextPendingConnection(), win.bring_front()))

    try:  # global kısayol (opsiyonel)
        from pynput import keyboard
        hk = keyboard.GlobalHotKeys({settings["hotkey"]: backend.ear.trigger})
        hk.daemon = True
        hk.start()
    except Exception as e:
        log.info("Global kısayol kapalı: %s", e)

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
