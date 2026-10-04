"""Wake word e$Yle$Ytirme: bulan$k e$Yle$Yme + Vosk'un s$k yanl$Y duydu$Yu bi$imler."""
from __future__ import annotations

import difflib
import re

from core.textutil import fold

CANON = "ultron"
ALIASES = {"ultron", "altron", "oltron", "ultran", "altran", "ultrun", "ultiron", "ultrom", "ulton", "ultra", "ultra on",
           "ultra an", "alt ron", "ult ron", "uc rol", "ucurol", "ucu rol", "uykusu rol", "eltron", "ltron", "outrun",
           "old run", "all drawn", "oh drawn", "or drawn", "always run", "well drawn"}
_EXACT = {"ultron", "altron", "oltron", "ultran", "ultrun"}

def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", fold(text))

def similarity(a: str, b: str = CANON) -> float:
    return difflib.SequenceMatcher(None, a, b).ratio()

def find_wake(text: str, threshold: float = 0.78):
    toks = _tokens(text)
    if not toks:
        return False, ""
    hit = None
    for i, t in enumerate(toks):
        for n in (3, 2):
            if i + n <= len(toks) and " ".join(toks[i:i + n]) in ALIASES:
                hit = (i, n)
                break
        if hit: break
        if t in _EXACT:
            hit = (i, 1)
            break
        if i < 3:
            joined = [(t, 1)]
            if i + 1 < len(toks):
                joined.append((t + toks[i + 1], 2))
            for cand, n in joined:
                if cand in ALIASES or (4 <= len(cand) <= 9 and "tr" in cand and similarity(cand) >= threshold):
                    hit = (i, n)
                    break
            if hit: break
    if not hit:
        return False, ""
    i, n = hit
    rest = toks[:i] + toks[i + n:]
    drop = {"hey", "merhaba", "selam", "uyan", "dinle", "acil", "ac"}
    while rest and rest[0] in drop and len(rest) > 1:
        rest = rest[1:]
    if rest and rest[0] in drop:
        rest = []
    return True, " ".join(rest)
