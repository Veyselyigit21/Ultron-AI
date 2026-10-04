"""Eylem (komut) kayıt defteri.

LLM'in yazdığı [CMD: AD: argüman] etiketleri burada ayrıştırılır ve çalıştırılır.
Sistem istemindeki komut listesi bu kayıttan otomatik üretilir; böylece yeni eklenen
(ör. kendi yazdığı) komutlar LLM tarafından da hemen bilinir.
"""
from __future__ import annotations

import re
import threading
from dataclasses import dataclass
from typing import Callable

from core.config import get_logger
from core.textutil import split_cmd_tags, strip_cmd_tags

log = get_logger("ultron.registry")
NAME_RE = re.compile(r"^[A-Z][A-Z0-9_]{1,31}$")


@dataclass
class Action:
    name: str
    func: Callable[[str], str]
    doc: str
    usage: str = ""
    danger: str = "safe"      # "safe" | "confirm"
    feedback: bool = False    # sonucu LLM'e geri verilsin mi (okuma/arama gibi)
    external: bool = False    # dış kaynaklı içerik getirir (enjeksiyon riski -> "taint")
    source: str = "core"      # "core" veya eklenti adı


class Registry:
    def __init__(self):
        self._a: dict[str, Action] = {}
        self._lock = threading.RLock()
        self._fails: dict[str, int] = {}
        self.on_plugin_failure: Callable[[str], None] | None = None

    # --- kayıt ---------------------------------------------------------
    def add(self, name, func, doc, usage="", danger="safe", feedback=False, external=False, source="core"):
        name = name.upper().strip()
        if not NAME_RE.match(name):
            raise ValueError(f"Geçersiz komut adı: {name!r}")
        if danger not in ("safe", "confirm"):
            raise ValueError("danger 'safe' veya 'confirm' olmalı")
        with self._lock:
            old = self._a.get(name)
            if old and old.source != source:
                raise ValueError(f"{name} komutu zaten '{old.source}' tarafından tanımlı")
            self._a[name] = Action(name, func, doc, usage or name, danger, feedback, external, source)

    def remove_source(self, source: str) -> int:
        with self._lock:
            names = [n for n, a in self._a.items() if a.source == source]
            for n in names:
                del self._a[n]
            self._fails.pop(source, None)
            return len(names)

    def get(self, name: str):
        return self._a.get(name.upper())

    def names(self):
        return sorted(self._a)

    def by_source(self, source: str):
        return [a for a in self._a.values() if a.source == source]

    # --- ayrıştırma ----------------------------------------------------
    @staticmethod
    def parse(text: str):
        """(etiketsiz_metin, [(AD, arg), ...])"""
        calls = [(n, a) for _, _, n, a in split_cmd_tags(text)]
        return strip_cmd_tags(text), calls

    # --- çalıştırma ----------------------------------------------------
    def run(self, name: str, arg: str) -> str:
        act = self.get(name)
        if not act:
            return f"{name} adında bir komut yok."
        try:
            out = act.func(arg)
            if act.source != "core":
                self._fails[act.source] = 0
            return "" if out is None else str(out)
        except Exception as e:  # eylem hatası asistanı düşürmemeli
            log.exception("Eylem hatası: %s", name)
            if act.source != "core":
                n = self._fails.get(act.source, 0) + 1
                self._fails[act.source] = n
                if n >= 3 and self.on_plugin_failure:
                    try:
                        self.on_plugin_failure(act.source)
                    except Exception:
                        pass
            return f"{name} çalışırken hata: {type(e).__name__}: {e}"

    # --- istem bloğu ---------------------------------------------------
    def prompt_block(self) -> str:
        lines = []
        for a in sorted(self._a.values(), key=lambda x: (x.source != "core", x.name)):
            tag = " (onay gerektirir)" if a.danger == "confirm" else ""
            lines.append(f"- [CMD: {a.usage}] → {a.doc}{tag}")
        return "\n".join(lines)


class PluginAPI:
    """Eklentilerin gördüğü daraltılmış yüzey: sadece komut ekleyebilirler."""

    def __init__(self, registry: Registry, source: str, force_confirm: bool = False):
        self._r, self._s, self._force = registry, source, force_confirm

    def add(self, name, func, doc, usage="", danger="safe", feedback=False):
        if not callable(func):
            raise TypeError("func çağrılabilir olmalı")
        self._r.add(name, func, doc, usage or name, "confirm" if self._force else danger,
                    feedback, external=False, source=self._s)
