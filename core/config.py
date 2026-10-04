"""Merkezi yapılandırma: yollar, kalıcı ayarlar, loglama.

Hiçbir yerde "D:\\ultron" gibi sabit yol yok; her şey bu dosyanın konumuna göre çözülür.
"""
from __future__ import annotations

import json
import logging
import os
import sys
import threading
from logging.handlers import RotatingFileHandler
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LOG_DIR = DATA_DIR / "logs"
TMP_DIR = DATA_DIR / "tmp"
SHOT_DIR = DATA_DIR / "screenshots"
MODELS_DIR = BASE_DIR / "models"
PLUGIN_DIR = BASE_DIR / "plugins"
ASSETS_DIR = BASE_DIR / "assets"
GUI_FILE = BASE_DIR / "gui" / "index_v2.html"

for _d in (DATA_DIR, LOG_DIR, TMP_DIR, SHOT_DIR, MODELS_DIR, PLUGIN_DIR):
    _d.mkdir(parents=True, exist_ok=True)

try:  # .env opsiyonel
    from dotenv import load_dotenv

    load_dotenv(BASE_DIR / ".env")
except Exception:  # pragma: no cover
    pass

IS_WIN = os.name == "nt"


def python_exe() -> str:
    """Çıktı yakalanabilsin diye pythonw.exe yerine python.exe döndürür."""
    exe = sys.executable
    if exe.lower().endswith("pythonw.exe"):
        cand = exe[:-11] + "python.exe"
        if os.path.exists(cand):
            return cand
    return exe


def atomic_write_json(path: Path, obj) -> None:
    tmp = Path(str(path) + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


DEFAULTS = {
    "owner_name": "Veysel",
    "home_city": "",                 # boşsa IP'den bulunur
    "mode": "auto",                  # auto | online | offline
    "online_model": "google/gemini-2.5-flash",
    "ollama_host": "http://localhost:11434",
    "ollama_model": "",              # boşsa yüklü modellerden otomatik seçilir
    "tts_voice": "tr-TR-AhmetNeural",
    "tts_offline_fallback": True,
    "stt_engine": "auto",            # auto | vosk | google
    "wake_threshold": 0.78,
    "wake_use_en": True,             # İngilizce model de wake word için dinlesin
    "conversation_window_s": 15,
    "confirm_dangerous": True,       # yıkıcı/geri alınamaz eylemlerde onay iste
    "confirm_plugins": True,         # eklenti kurulumunda her zaman onay iste
    "mic_device": None,
    "hotkey": "<ctrl>+<alt>+u",
}


class Settings:
    def __init__(self, path: Path | None = None):
        self._path = path or (DATA_DIR / "settings.json")
        self._lock = threading.RLock()
        self._d = dict(DEFAULTS)
        try:
            if self._path.exists():
                with open(self._path, "r", encoding="utf-8") as f:
                    self._d.update(json.load(f))
        except Exception:
            pass

    def get(self, key, default=None):
        with self._lock:
            return self._d.get(key, default)

    __getitem__ = get

    def set(self, key, value) -> None:
        with self._lock:
            self._d[key] = value
            try:
                atomic_write_json(self._path, self._d)
            except Exception:
                pass


settings = Settings()


def _make_logger(name: str, filename: str) -> logging.Logger:
    lg = logging.getLogger(name)
    if not lg.handlers:
        lg.setLevel(logging.INFO)
        h = RotatingFileHandler(LOG_DIR / filename, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
        h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        lg.addHandler(h)
        lg.propagate = False
    return lg


def get_logger(name: str = "ultron") -> logging.Logger:
    return _make_logger(name, "ultron.log")


def audit(msg: str) -> None:
    """Çalıştırılan her eylemin denetim kaydı (data/logs/actions.log)."""
    _make_logger("ultron.audit", "actions.log").info(msg)
