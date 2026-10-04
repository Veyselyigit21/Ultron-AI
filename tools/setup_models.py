"""Vosk modellerini (TR + EN) doğrular; eksik/bozuksa resmi kaynaktan indirir.

Kullanım:  python tools/setup_models.py          # eksikleri indir
           python tools/setup_models.py --force  # yeniden indir
"""
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core import models  # noqa: E402


def bar(p):
    print(f"\r  %{int(p * 100):3d}", end="", flush=True)


def main():
    force = "--force" in sys.argv
    for kind in ("tr", "en"):
        cur = models.find_model(kind)
        if cur and not force:
            print(f"[{kind.upper()}] hazır: {cur}")
            continue
        print(f"[{kind.upper()}] {models.diagnose(kind) if not cur else 'yeniden indiriliyor'}")
        if force:
            shutil.rmtree(models.MODELS_DIR / f"vosk-{kind}", ignore_errors=True)
        try:
            p = models.download(kind, progress=bar)
            print(f"\n[{kind.upper()}] kuruldu: {p}")
        except Exception as e:
            print(f"\n[{kind.upper()}] indirilemedi: {e}")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
