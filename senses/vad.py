"""Basit, bağımlılıksız konuşma bölütleyici (adaptif enerji eşiği).

Sessizken tanıma yapılmaz → CPU boşta ~0. Konuşma bitince tek parça (segment) döner.
"""
from __future__ import annotations

from collections import deque

import numpy as np


def rms(frame: bytes) -> float:
    a = np.frombuffer(frame, dtype=np.int16).astype(np.float32)
    return float(np.sqrt(np.mean(a * a))) if a.size else 0.0


class Segmenter:
    def __init__(self, frame_ms=100, min_thr=250.0, end_silence_frames=7, min_frames=3, max_frames=120, pre_roll=3):
        self.frame_ms = frame_ms
        self.min_thr = min_thr
        self.end_silence = end_silence_frames
        self.min_frames = min_frames
        self.max_frames = max_frames
        self.noise = 150.0
        self._pre = deque(maxlen=pre_roll)
        self.reset()

    def reset(self):
        self._buf: list[bytes] = []
        self._in = False
        self._silence = 0
        self._hot = 0
        self._pre.clear()

    @property
    def threshold(self) -> float:
        return max(self.min_thr, self.noise * 2.8)

    @property
    def in_speech(self) -> bool:
        return self._in

    def feed(self, frame: bytes):
        """Her 100 ms'lik çerçeve için çağrılır. Konuşma bitince PCM bytes döner, yoksa None."""
        level = rms(frame)
        thr = self.threshold
        if not self._in:
            self._pre.append(frame)
            if level > thr:
                self._hot += 1
                if self._hot >= 2:
                    self._in = True
                    self._buf = list(self._pre)
                    self._silence = 0
            else:
                self._hot = 0
                self.noise = 0.97 * self.noise + 0.03 * level  # gürültü tabanını yalnızca sessizken öğren
            return None
        self._buf.append(frame)
        self._silence = self._silence + 1 if level < thr * 0.6 else 0
        if self._silence >= self.end_silence or len(self._buf) >= self.max_frames:
            voiced = len(self._buf) - self._silence
            seg = b"".join(self._buf) if voiced >= self.min_frames else None
            self.reset()
            return seg
        return None
