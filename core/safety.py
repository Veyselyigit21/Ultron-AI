"""Güvenlik katmanı: onay verilse bile ASLA çalıştırılmayacak komutlar ve korumalı yollar."""
import os
import re
from pathlib import Path

from core.config import BASE_DIR, DATA_DIR

_CATASTROPHIC = [
    (r"\bformat(\.com)?\s+[a-z]:", "disk biçimlendirme"),
    (r"\b(format-volume|clear-disk|initialize-disk|remove-partition)\b", "disk/bölüm silme"),
    (r"\bdiskpart\b", "diskpart"),
    (r"\b(bcdedit|bootrec)\b", "önyükleme ayarı değiştirme"),
    (r"\bvssadmin\s+delete", "gölge kopya silme"),
    (r"\bcipher\s+/w", "disk silme (cipher /w)"),
    (r"\breg(\.exe)?\s+delete\s+hk(lm|cr)", "sistem kayıt defteri silme"),
    (r"\b(takeown|icacls)\b.*[a-z]:\\(windows|program files)", "sistem klasörü izinleri"),
    (r"\b(rd|rmdir|del|erase)\b.*\s[a-z]:\\?(\s|$|[\"'])", "sürücü kökünü silme"),
    (r"\b(rd|rmdir|del|erase)\b.*[a-z]:\\windows", "Windows klasörünü silme"),
    (r"remove-item\b.*-recurse.*\s[a-z]:\\?(\s|$|[\"'])", "sürücü kökünü silme"),
    (r"remove-item\b.*-recurse.*[a-z]:\\windows", "Windows klasörünü silme"),
    (r"\brm\s+(-[a-z]*\s+)*-[a-z]*r[a-z]*\s+(-[a-z]+\s+)*(/|~|\*|/\*|\$home)(\s|$)", "rm -rf kök/ev dizini"),
    (r":\(\)\s*\{\s*:\|:&\s*\};:", "fork bomb"),
    (r"\bdd\s+.*of=/dev/(sd|nvme|hd)", "disk üzerine yazma"),
]


def is_catastrophic(cmd: str):
    """Yasaklı desenle eşleşirse sebebi döner, değilse None."""
    low = " ".join(cmd.lower().split())
    for pat, why in _CATASTROPHIC:
        if re.search(pat, low):
            return why
    return None


def _norm(p) -> str:
    return os.path.normcase(os.path.abspath(str(p)))


def protected_reason(path):
    """Silme/taşıma/yazma için korumalı yolları açıklamasıyla döner."""
    p = _norm(path)
    drive_root = os.path.splitdrive(p)[0] + os.sep
    if p == _norm(drive_root) or p == _norm("/"):
        return "sürücü kökü"
    home = _norm(Path.home())
    if p == home:
        return "kullanıcı ana klasörü"
    for env in ("WINDIR", "ProgramFiles", "ProgramFiles(x86)", "ProgramData"):
        v = os.environ.get(env)
        if v and (p == _norm(v) or p.startswith(_norm(v) + os.sep)):
            return "sistem/program klasörü"
    if os.name != "nt":
        for v in ("/bin", "/sbin", "/usr", "/etc", "/boot", "/lib", "/var", "/sys", "/proc", "/dev"):
            if p == v or p.startswith(v + os.sep):
                return "sistem klasörü"
    base = _norm(BASE_DIR)
    data = _norm(DATA_DIR)
    if p == base or (p.startswith(base + os.sep) and not (p == data or p.startswith(data + os.sep))):
        return "ULTRON'un kendi kaynak kodu (değişiklik sadece eklenti hattıyla yapılır)"
    return None
