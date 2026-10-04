"""ULTRON'un kulağı: sürekli dinler, "Ultron" der demez uyanır, sohbet penceresinde wake word istemez.

Mimari (eski sürümden farklar):
- Tek süreç, tek mikrofon akışı (eski: daemon + GUI iki ayrı akış, GUI her uyanışta yeniden açılıyordu).
- VAD ile konuşma bölütlenir; sessizken Vosk çalışmaz. Kısmi (partial) sonuçlarla tetikleme yok → çift tetikleme yok.
- Komut metni internet varsa Google STT (çok daha doğru), yoksa Vosk ile çevrilir.
- ULTRON konuşurken mikrofon yok sayılır (kendi sesini duyup tetiklenmez).
- Sohbet modu gerçekten çalışır: uyandıktan sonra N saniye wake word gerekmez.
"""
from __future__ import annotations

import json
import queue
import threading
import time
from typing import Callable

from core import models, net
from core.config import get_logger, settings
from senses.vad import Segmenter, rms
from senses.wake import find_wake

log = get_logger("ultron.ear")
SR = 16000
FRAME = 1600  # 100 ms


class BackgroundEar:
    def __init__(self, on_wake: Callable[[], None], on_command: Callable[[str], None],
                 on_level: Callable[[float], None] | None = None, on_state: Callable[[str], None] | None = None,
                 on_error: Callable[[str], None] | None = None, mouth=None):
        self.on_wake, self.on_command = on_wake, on_command
        self.on_level = on_level or (lambda v: None)
        self.on_state = on_state or (lambda s: None)
        self.on_error = on_error or (lambda m: None)
        self.mouth = mouth
        self.running = False
        self.paused = False
        self._q: "queue.Queue[bytes]" = queue.Queue(maxsize=200)
        self._convo_until = 0.0
        self._last_wake = 0.0
        self._state = ""
        self._tr = self._en = None
        self._seg = Segmenter(frame_ms=100)

    # ───────── dış API ─────────
    def start(self) -> None:
        if self.running:
            return
        self.running = True
        threading.Thread(target=self._loop, daemon=True, name="ear").start()

    def stop(self) -> None:
        self.running = False

    def pause(self) -> None:
        self.paused = True

    def resume(self) -> None:
        self.paused = False
        self._drain()

    def trigger(self) -> None:
        """Kısayol/tray ile elle uyandırma: wake word gerekmeden sohbet moduna girer."""
        self._enter_conversation()
        self.on_wake()

    def extend_conversation(self) -> None:
        """ULTRON cevabı bitirince çağrılır; takip sorusu için pencereyi yeniler."""
        if time.time() < self._convo_until + 60:
            self._convo_until = time.time() + settings["conversation_window_s"]

    # ───────── iç ─────────
    def _set_state(self, s: str) -> None:
        if s != self._state:
            self._state = s
            self.on_state(s)

    def _enter_conversation(self) -> None:
        self._convo_until = time.time() + settings["conversation_window_s"]
        self._set_state("awake")

    def _drain(self) -> None:
        while True:
            try:
                self._q.get_nowait()
            except queue.Empty:
                break
        self._seg.reset()

    def _load_models(self) -> bool:
        try:
            from vosk import KaldiRecognizer, Model, SetLogLevel
            SetLogLevel(-1)
        except Exception as e:
            self.on_error(f"Vosk yüklenemedi: {e}  (pip install vosk)")
            return False
        self._set_state("loading")
        tr = models.find_model("tr")
        if not tr:
            self.on_error(models.diagnose("tr") + " — internet varsa otomatik indirmeyi deniyorum…")
            tr = models.ensure("tr")
        if not tr:
            self.on_error("TR Vosk modeli yok; sadece Google STT ile (internet gerekir) çalışabilirim.")
        else:
            self._tr = KaldiRecognizer(Model(str(tr)), SR)
        if settings["wake_use_en"]:
            en = models.find_model("en")
            if en:
                try:
                    self._en = KaldiRecognizer(Model(str(en)), SR)
                except Exception as e:
                    log.warning("EN model yüklenemedi: %s", e)
        return True

    @staticmethod
    def _vosk_text(rec, pcm: bytes) -> str:
        if rec is None:
            return ""
        rec.AcceptWaveform(pcm)
        return json.loads(rec.FinalResult()).get("text", "").strip()

    def _google_text(self, pcm: bytes) -> str:
        import speech_recognition as sr
        r = sr.Recognizer()
        r.operation_timeout = 7
        try:
            return r.recognize_google(sr.AudioData(pcm, SR, 2), language="tr-TR").strip()
        except sr.UnknownValueError:
            return ""
        except sr.RequestError as e:
            net.mark(False)
            log.warning("Google STT ulaşılamadı: %s", e)
            raise

    def _transcribe(self, pcm: bytes) -> str:
        eng = settings["stt_engine"]
        if eng in ("auto", "google") and net.is_online():
            try:
                t = self._google_text(pcm)
                if t or eng == "google":
                    return t
            except Exception:
                pass
        return self._vosk_text(self._tr, pcm)

    def _handle(self, pcm: bytes) -> None:
        now = time.time()
        convo = now < self._convo_until
        if convo:
            self._set_state("hearing")
            text = self._transcribe(pcm)
            if not text:
                self._set_state("awake")
                return
            found, rest = find_wake(text, settings["wake_threshold"])
            if found:
                text = rest
                if not text:
                    self._enter_conversation()
                    self.on_wake()
                    return
            self._enter_conversation()
            self.on_command(text)
            return

        # uyku: yalnızca wake word ara
        t_tr = self._vosk_text(self._tr, pcm)
        found, rest = find_wake(t_tr, settings["wake_threshold"])
        if not found and self._en is not None:
            t_en = self._vosk_text(self._en, pcm)
            found, rest = find_wake(t_en, settings["wake_threshold"])
            t_tr = t_en if found else t_tr
        if not found and self._tr is None and net.is_online():  # Vosk yoksa Google ile ara
            try:
                found, rest = find_wake(self._google_text(pcm), settings["wake_threshold"])
            except Exception:
                pass
        if not found:
            return
        if now - self._last_wake < 2.0:
            return
        self._last_wake = now
        log.info("Wake word: %r", t_tr)
        seconds = len(pcm) / (SR * 2)
        cmd = rest
        if seconds > 1.6 or rest:  # aynı nefeste komut verilmiş olabilir → daha doğru çeviri
            if net.is_online() and settings["stt_engine"] != "vosk":
                try:
                    g = self._google_text(pcm)
                    f2, r2 = find_wake(g, settings["wake_threshold"])
                    cmd = r2 if f2 else cmd
                except Exception:
                    pass
        self._enter_conversation()
        self.on_wake()
        if cmd:
            self.on_command(cmd)

    def _loop(self) -> None:
        try:
            self._load_models()
        except Exception as e:
            log.exception("Model yükleme hatası")
            self.on_error(f"Ses modelleri yüklenemedi: {e}")
        import sounddevice as sd

        def cb(indata, frames, t, status):
            try:
                self._q.put_nowait(bytes(indata))
            except queue.Full:
                pass

        self._set_state("sleep")
        mute_until = 0.0
        while self.running:
            try:
                with sd.RawInputStream(samplerate=SR, blocksize=FRAME, dtype="int16", channels=1,
                                       device=settings["mic_device"], callback=cb):
                    log.info("Mikrofon akışı açıldı")
                    while self.running:
                        try:
                            data = self._q.get(timeout=0.3)
                        except queue.Empty:
                            if self._state in ("awake", "hearing") and time.time() > self._convo_until:
                                self._set_state("sleep")
                            continue
                        if self.paused or (self.mouth is not None and self.mouth.speaking):
                            self._seg.reset()
                            mute_until = time.time() + 0.6
                            continue
                        if time.time() < mute_until:
                            continue
                        self.on_level(rms(data))
                        seg = self._seg.feed(data)
                        if self._state in ("awake", "hearing") and time.time() > self._convo_until and not self._seg.in_speech:
                            self._set_state("sleep")
                        if seg:
                            try:
                                self._handle(seg)
                            except Exception:
                                log.exception("Segment işlenemedi")
            except Exception as e:
                log.warning("Mikrofon hatası: %s", e)
                self.on_error(f"Mikrofon açılamadı: {e} (5 sn sonra tekrar denenecek)")
                time.sleep(5)
