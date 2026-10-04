"""ULTRON'un ağzı: edge-tts (online) + pyttsx3/SAPI (offline yedek), cümle cümle akıtma.

Eski sürümden farklar: her cümle için yeni Python süreci açılmaz; sentez ile oynatma paralel yürür;
"konuşuyor" durumu gerçek ses çalma süresini kapsar (orb animasyonu doğru senkron olur); internet yoksa
otomatik offline sese geçer.
"""
from __future__ import annotations

import asyncio
import os
import queue
import threading
import time
import uuid
from typing import Callable

from core.config import TMP_DIR, get_logger, settings
from core.net import is_online, mark
from core.textutil import speech_clean, split_sentences

log = get_logger("ultron.voice")


class Mouth:
    def __init__(self, on_state: Callable[[bool], None] | None = None):
        self.on_state = on_state or (lambda s: None)
        self._synth_q: "queue.Queue[tuple[int, str]]" = queue.Queue()
        self._play_q: "queue.Queue[tuple[int, str]]" = queue.Queue(maxsize=3)
        self._gen = 0
        self._pending = 0
        self._lock = threading.Lock()
        self._speaking = False
        self._last_end = 0.0
        self._offline_engine_ok = None
        for f in TMP_DIR.glob("voice_*"):  # eski artıklar
            try:
                f.unlink()
            except OSError:
                pass
        threading.Thread(target=self._synth_loop, daemon=True, name="tts-synth").start()
        threading.Thread(target=self._play_loop, daemon=True, name="tts-play").start()

    # ───────── dış API ─────────
    @property
    def speaking(self) -> bool:
        return self._speaking or self._pending > 0

    @property
    def idle_for(self) -> float:
        """Konuşma bitiminden beri geçen saniye (kulak yankı koruması için)."""
        return 0.0 if self.speaking else time.time() - self._last_end

    def speak(self, text: str) -> None:
        clean = speech_clean(text or "")
        if not clean:
            return
        chunks = split_sentences(clean)
        with self._lock:
            gen = self._gen
            self._pending += len(chunks)
        for c in chunks:
            self._synth_q.put((gen, c))

    def interrupt(self) -> None:
        with self._lock:
            self._gen += 1
            self._pending = 0
        for q in (self._synth_q, self._play_q):
            while True:
                try:
                    item = q.get_nowait()
                    if q is self._play_q:
                        self._rm(item[1])
                except queue.Empty:
                    break
        try:
            import pygame
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
        except Exception:
            pass

    def wait_done(self, timeout: float = 60.0) -> None:
        t0 = time.time()
        while self.speaking and time.time() - t0 < timeout:
            time.sleep(0.05)

    # ───────── sentez ─────────
    @staticmethod
    def _rm(path: str) -> None:
        try:
            os.remove(path)
        except OSError:
            pass

    def _synth_edge(self, text: str, out: str) -> bool:
        try:
            import edge_tts

            async def go():
                await asyncio.wait_for(edge_tts.Communicate(text, settings["tts_voice"]).save(out), timeout=15)

            asyncio.run(go())
            return os.path.exists(out) and os.path.getsize(out) > 0
        except Exception as e:
            log.warning("edge-tts başarısız: %s", e)
            mark(False)
            return False

    def _synth_offline(self, text: str, out: str) -> bool:
        if self._offline_engine_ok is False or not settings["tts_offline_fallback"]:
            return False
        try:
            import pyttsx3
            eng = pyttsx3.init()
            for v in eng.getProperty("voices"):
                blob = f"{v.id} {v.name} {getattr(v, 'languages', '')}".lower()
                if "tr" in blob.split() or "turk" in blob or "tolga" in blob or "filiz" in blob or "tr-tr" in blob:
                    eng.setProperty("voice", v.id)
                    break
            eng.setProperty("rate", 175)
            eng.save_to_file(text, out)
            eng.runAndWait()
            eng.stop()
            self._offline_engine_ok = os.path.exists(out) and os.path.getsize(out) > 0
            return bool(self._offline_engine_ok)
        except Exception as e:
            log.warning("Offline TTS başarısız: %s", e)
            self._offline_engine_ok = False
            return False

    def _synth_loop(self) -> None:
        while True:
            gen, text = self._synth_q.get()
            if gen != self._gen:
                continue
            base = TMP_DIR / f"voice_{uuid.uuid4().hex[:8]}"
            path = None
            if is_online() and self._synth_edge(text, str(base) + ".mp3"):
                path = str(base) + ".mp3"
            elif self._synth_offline(text, str(base) + ".wav"):
                path = str(base) + ".wav"
            if not path:
                with self._lock:
                    self._pending = max(0, self._pending - 1)
                continue
            if gen != self._gen:
                self._rm(path)
                continue
            self._play_q.put((gen, path))

    # ───────── oynatma ─────────
    def _set_speaking(self, s: bool) -> None:
        if s != self._speaking:
            self._speaking = s
            if not s:
                self._last_end = time.time()
            try:
                self.on_state(s)
            except Exception:
                pass

    def _play_loop(self) -> None:
        try:
            import pygame
        except Exception as e:
            log.error("pygame yok, ses çalınamaz: %s", e)
            return
        while True:
            gen, path = self._play_q.get()
            try:
                if gen != self._gen:
                    continue
                if not pygame.mixer.get_init():
                    pygame.mixer.init()
                self._set_speaking(True)
                pygame.mixer.music.load(path)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy() and gen == self._gen:
                    time.sleep(0.03)
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()
            except Exception as e:
                log.warning("Oynatma hatası: %s", e)
            finally:
                self._rm(path)
                with self._lock:
                    self._pending = max(0, self._pending - 1)
                if self._play_q.empty() and self._synth_q.empty() and self._pending == 0:
                    self._set_speaking(False)
