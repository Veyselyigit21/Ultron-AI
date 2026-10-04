"""Vosk modellerini bulur, doğrular ve gerekirse indirir.

Depodaki model klasörü bozuk yapıdaysa (am/, conf/, graph/ yok) burada tespit edilir.
"""
from __future__ import annotations

import io
import os
import shutil
import urllib.request
import zipfile
from pathlib import Path

from core.config import BASE_DIR, MODELS_DIR, get_logger

log = get_logger("ultron.models")

URLS = {
    "tr": "https://alphacephei.com/vosk/models/vosk-model-small-tr-0.3.zip",
    "en": "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip",
}
CANDIDATES = {
    "tr": [MODELS_DIR / "vosk-tr", BASE_DIR / "vosk-model-small-tr-0.3"],
    "en": [MODELS_DIR / "vosk-en", BASE_DIR / "vosk-model-en"],
}


def is_valid(path: Path) -> bool:
    return ((path / "am" / "final.mdl").exists() and (path / "conf" / "model.conf").exists()) or \
           ((path / "final.mdl").exists() and (path / "mfcc.conf").exists())


def _unwrap(path: Path) -> Path | None:
    """Zip çıkarılınca bir üst klasör daha oluşabilir; içindeki gerçek kökü bulur."""
    if is_valid(path):
        return path
    if path.is_dir():
        for sub in path.iterdir():
            if sub.is_dir() and is_valid(sub):
                return sub
    return None


def find_model(kind: str) -> Path | None:
    for c in CANDIDATES[kind]:
        if c.exists():
            p = _unwrap(c)
            if p:
                return p
    return None


def diagnose(kind: str) -> str:
    for c in CANDIDATES[kind]:
        if c.exists() and not _unwrap(c):
            return (f"'{c}' klasörü var ama geçerli bir Vosk modeli değil "
                    f"(final.mdl bulunamadı). Yeniden indir: python tools/setup_models.py")
    return f"Vosk {kind.upper()} modeli bulunamadı. İndir: python tools/setup_models.py"


def download(kind: str, url: str | None = None, progress=None) -> Path:
    """Resmi Vosk modelini indirip models/vosk-<kind> altına açar."""
    url = url or URLS[kind]
    dest = MODELS_DIR / f"vosk-{kind}"
    log.info("Model indiriliyor: %s", url)
    buf = io.BytesIO()
    with urllib.request.urlopen(url, timeout=60) as r:
        total = int(r.headers.get("Content-Length") or 0)
        got = 0
        while True:
            chunk = r.read(1 << 16)
            if not chunk:
                break
            buf.write(chunk)
            got += len(chunk)
            if progress and total:
                progress(got / total)
    buf.seek(0)
    tmp = MODELS_DIR / f"_extract_{kind}"
    shutil.rmtree(tmp, ignore_errors=True)
    with zipfile.ZipFile(buf) as z:
        z.extractall(tmp)
    root = _unwrap(tmp)
    if not root:
        shutil.rmtree(tmp, ignore_errors=True)
        raise RuntimeError("İndirilen arşiv geçerli bir Vosk modeli içermiyor")
    shutil.rmtree(dest, ignore_errors=True)
    shutil.move(str(root), str(dest))
    shutil.rmtree(tmp, ignore_errors=True)
    return dest


def ensure(kind: str, progress=None) -> Path | None:
    p = find_model(kind)
    if p:
        return p
    try:
        return download(kind, progress=progress)
    except Exception as e:
        log.warning("Model indirilemedi (%s): %s", kind, e)
        return None
