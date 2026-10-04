"""Uzun süreli hafıza: basit, bağımlılıksız anlamsal (kelime örtüşmesi) arama."""
from __future__ import annotations

import json
import threading
import time
from pathlib import Path

from core.config import BASE_DIR, DATA_DIR, atomic_write_json
from core.textutil import words

_STOP = {"ve", "bir", "bu", "su", "o", "ben", "sen", "de", "da", "mi", "mu", "icin", "ile", "ne", "ama", "gibi", "cok", "daha"}


class MemoryVault:
    MAX = 1000

    def __init__(self, path: Path | None = None):
        self.path = Path(path) if path else DATA_DIR / "long_term_memory.json"
        self._lock = threading.RLock()
        self.items: list[dict] = []
        self._load()

    def _load(self):
        src = self.path
        legacy = BASE_DIR / "long_term_memory.json"
        if not src.exists() and legacy.exists():  # eski sürümden taşı
            src = legacy
        try:
            if src.exists():
                raw = json.loads(src.read_text(encoding="utf-8"))
                for r in raw:
                    if isinstance(r, str):
                        self.items.append({"t": 0, "text": r})
                    elif isinstance(r, dict) and r.get("text"):
                        self.items.append({"t": r.get("t", 0), "text": r["text"]})
        except Exception:
            self.items = []

    def _save(self):
        try:
            atomic_write_json(self.path, self.items)
        except Exception:
            pass

    def archive(self, text: str) -> bool:
        text = (text or "").strip()
        if len(text) < 5:
            return False
        with self._lock:
            self.items.append({"t": int(time.time()), "text": text})
            self.items = self.items[-self.MAX:]
            self._save()
        return True

    @staticmethod
    def _tok(s: str) -> set:
        return {w for w in words(s) if w not in _STOP and len(w) > 1}

    def search(self, query: str, top_k: int = 2, min_score: float = 0.12) -> list[str]:
        q = self._tok(query)
        if not q:
            return []
        scored = []
        with self._lock:
            for it in self.items:
                m = self._tok(it["text"])
                if not m:
                    continue
                score = len(q & m) / len(q | m)
                if score >= min_score:
                    scored.append((score, it["text"]))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [t for _, t in scored[:top_k]]
