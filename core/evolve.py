"""Kendini geliştirme: LLM'e yeni yetenek (eklenti) yazdırır, doğrular, kurar, sıcak yükler.

Akış:  istek → (arka planda) kod üret → AST ile doğrula → plugins/_pending/ içine yaz →
       kullanıcıdan onay → pip paketlerini kur → ayrı süreçte duman testi → plugins/ içine al →
       komutları anında kaydet (yeniden başlatma yok).

Güvenlik: Üretilen kod kullanıcı yetkisiyle çalışır; bu yüzden onaysız kurulmaz. Çekirdek dosyalar
(core/, senses/, actions/, main_gui.py) değiştirilmez, sadece plugins/ genişler. Hash uyuşmazlığı,
art arda hata ve manuel kaldırma için geri alma mekanizması vardır.
"""
from __future__ import annotations

import ast
import hashlib
import importlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import threading
import time

from core.config import IS_WIN, PLUGIN_DIR, atomic_write_json, get_logger, python_exe
from core.net import is_online
from core.registry import NAME_RE, PluginAPI

log = get_logger("ultron.evolve")

PENDING_DIR = PLUGIN_DIR / "_pending"
REMOVED_DIR = PLUGIN_DIR / "_removed"
MANIFEST = PLUGIN_DIR / "manifest.json"
REQ_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._\-]*(\[[A-Za-z0-9,_\-]+\])?([=<>!~]=?[A-Za-z0-9.*]+(,[=<>!~]=?[A-Za-z0-9.*]+)*)?$")
RISKY_MODULES = {"subprocess", "os", "shutil", "ctypes", "socket", "requests", "urllib", "http", "pyautogui",
                 "winreg", "sys", "importlib", "pickle", "marshal", "pathlib", "sqlite3", "smtplib", "ftplib"}
FORBIDDEN_MODULES = {"core", "senses", "actions", "main_gui", "builtins"}
FORBIDDEN_CALLS = {"eval", "exec", "compile", "__import__"}

SPEC = '''Sen ULTRON adlı Windows masaüstü asistanı için Python eklentisi yazan bir mühendissin.
Kullanıcının istediği yeteneği TEK bir Python dosyası olarak yaz. SADECE ```python bloğu döndür.

KURALLAR:
- Dosyanın üst düzeyinde sadece: import'lar, sabitler, fonksiyon/sınıf tanımları ve docstring olsun. Üst düzeyde çağrı/çalıştırma YOK.
- Zorunlu: `def register(reg):` — içinde `reg.add(AD, fonksiyon, "ne yapar", usage="AD: argüman")` ile komut(lar) kaydet.
  AD: BÜYÜK_HARF_VE_ALT_ÇİZGİ, 2-32 karakter. Şu adlar ZATEN VAR, kullanma: {existing}
- Komut fonksiyonu `def f(arg: str) -> str` imzalı olmalı, kullanıcıya söylenecek KISA Türkçe bir metin döndürmeli.
  Dış veri döndürüp asistanın görmesi gerekiyorsa reg.add(..., feedback=True) ver.
- Yıkıcı/geri alınamaz iş yapıyorsa danger="confirm" ver.
- Üçüncü parti paket gerekiyorsa üst düzeyde `REQUIREMENTS = ["paket1", "paket2"]` (en çok 4, sadece PyPI adları).
- Hedef: Windows 10/11, Python 3.10+. `core`, `senses`, `actions` modüllerini import etme. eval/exec/__import__ kullanma.
- Hata durumunda istisna fırlatma; anlaşılır bir Türkçe mesaj döndür.

ÖRNEK:
```python
"""Rastgele sayı üretir."""
import random

def _roll(arg: str) -> str:
    try:
        n = int(arg or 6)
    except ValueError:
        return "Sayı anlayamadım."
    return f"{{random.randint(1, max(2, n))}} geldi."

def register(reg):
    reg.add("ZAR_AT", _roll, "Zar atar", usage="ZAR_AT: kaç yüzlü")
```
'''

SMOKE = r'''
import importlib.util, json, sys
spec = importlib.util.spec_from_file_location("ultron_plugin_smoke", sys.argv[1])
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
names = []
class R:
    def add(self, name, func, doc, usage="", danger="safe", feedback=False):
        assert callable(func), "func çağrılabilir değil"
        names.append(name)
mod.register(R())
print("SMOKE_OK " + json.dumps(names))
'''


def extract_code(raw: str) -> str:
    m = re.findall(r"```(?:python|py)?\s*\n(.*?)```", raw, re.S)
    if m:
        return max(m, key=len).strip() + "\n"
    return raw.strip() + "\n"


def sha256(path) -> str:
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


class Validation:
    def __init__(self):
        self.errors: list[str] = []
        self.flags: list[str] = []
        self.commands: list[str] = []
        self.requirements: list[str] = []
        self.doc: str = ""


def validate(code: str, existing: set[str]) -> Validation:
    v = Validation()
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        v.errors.append(f"Sözdizimi hatası: satır {e.lineno}: {e.msg}")
        return v
    v.doc = (ast.get_docstring(tree) or "").strip().splitlines()[0] if ast.get_docstring(tree) else ""
    has_register = False
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef,
                             ast.Assign, ast.AnnAssign)):
            if isinstance(node, ast.FunctionDef) and node.name == "register":
                has_register = len(node.args.args) == 1
            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "REQUIREMENTS" for t in node.targets):
                try:
                    reqs = ast.literal_eval(node.value)
                    assert isinstance(reqs, list) and all(isinstance(r, str) for r in reqs)
                    v.requirements = reqs
                except Exception:
                    v.errors.append("REQUIREMENTS düz bir string listesi olmalı")
            continue
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            continue
        v.errors.append(f"Üst düzeyde kod çalıştırma yasak (satır {node.lineno}); sadece tanım olmalı")
    if not has_register:
        v.errors.append("`def register(reg):` (tek parametreli) bulunamadı")
    if len(v.requirements) > 4:
        v.errors.append("En çok 4 paket istenebilir")
    for r in v.requirements:
        if not REQ_RE.match(r):
            v.errors.append(f"Geçersiz paket adı: {r!r}")
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods = [a.name.split(".")[0] for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            mods = [(node.module or "").split(".")[0]]
        else:
            mods = []
        for m in mods:
            if m in FORBIDDEN_MODULES:
                v.errors.append(f"`{m}` modülü import edilemez")
            elif m in RISKY_MODULES and m not in v.flags:
                v.flags.append(m)
        if isinstance(node, ast.Call):
            fn = node.func
            nm = fn.id if isinstance(fn, ast.Name) else (fn.attr if isinstance(fn, ast.Attribute) else "")
            if nm in FORBIDDEN_CALLS:
                v.errors.append(f"`{nm}()` kullanımı yasak (satır {node.lineno})")
            if nm == "open" and len(node.args) >= 2 and isinstance(node.args[1], ast.Constant) \
                    and any(c in str(node.args[1].value) for c in "wax") and "dosya yazma" not in v.flags:
                v.flags.append("dosya yazma")
            if nm == "add" and isinstance(fn, ast.Attribute) and node.args and isinstance(node.args[0], ast.Constant) \
                    and isinstance(node.args[0].value, str):
                v.commands.append(node.args[0].value.upper())
    if not v.commands:
        v.errors.append("`reg.add(...)` ile hiç komut kaydedilmiyor")
    for c in v.commands:
        if not NAME_RE.match(c):
            v.errors.append(f"Geçersiz komut adı: {c}")
        elif c in existing:
            v.errors.append(f"{c} komutu zaten var")
    return v


class EvolutionManager:
    def __init__(self, brain):
        self.brain = brain
        self.reg = brain.reg
        self.s = brain.s
        self.loaded: dict[str, object] = {}
        self._busy = False
        self.reg.on_plugin_failure = self._auto_disable
        for d in (PENDING_DIR, REMOVED_DIR):
            d.mkdir(parents=True, exist_ok=True)
        A = self.reg.add
        A("EVOLVE", self.evolve_action, "Yeni bir yetenek yazıp kendine ekler (kendini geliştirme)", "EVOLVE: istenen özellik")
        A("PLUGIN_LIST", self.list_action, "Kurulu eklentileri listeler", "PLUGIN_LIST")
        A("PLUGIN_SHOW", self.show_action, "Bir eklentinin kodunu gösterir", "PLUGIN_SHOW: ad", feedback=True)
        A("PLUGIN_REMOVE", self.remove_action, "Eklentiyi kaldırır (geri alınabilir)", "PLUGIN_REMOVE: ad", danger="confirm")
        self.load_all()

    # ───────── manifest ─────────
    def _manifest(self) -> dict:
        try:
            return json.loads(MANIFEST.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _save_manifest(self, m: dict) -> None:
        atomic_write_json(MANIFEST, m)

    # ───────── yükleme ─────────
    def _load_file(self, name: str, path, flags) -> list[str]:
        spec = importlib.util.spec_from_file_location(f"ultron_plugin_{name}", str(path))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.register(PluginAPI(self.reg, name, force_confirm=bool(flags)))
        self.loaded[name] = mod
        return [a.name for a in self.reg.by_source(name)]

    def load_all(self) -> None:
        m = self._manifest()
        for name, info in m.items():
            if not info.get("enabled", True):
                continue
            path = PLUGIN_DIR / f"{name}.py"
            try:
                if not path.exists():
                    raise FileNotFoundError("dosya yok")
                if sha256(path) != info.get("sha256"):
                    raise RuntimeError("dosya onaylandıktan sonra değiştirilmiş (hash uyuşmuyor)")
                self._load_file(name, path, info.get("flags"))
                log.info("Eklenti yüklendi: %s", name)
            except Exception as e:
                log.warning("Eklenti yüklenemedi %s: %s", name, e)
                info["last_error"] = str(e)
                self.brain.notify(f"'{name}' eklentisi yüklenmedi: {e}")
        self._save_manifest(m)

    def _auto_disable(self, name: str) -> None:
        self.disable(name, reason="art arda hata verdi")
        self.brain.notify(f"'{name}' eklentisi art arda hata verdiği için devre dışı bırakıldı.")

    def disable(self, name: str, reason: str = "") -> None:
        self.reg.remove_source(name)
        self.loaded.pop(name, None)
        m = self._manifest()
        if name in m:
            m[name]["enabled"] = False
            m[name]["last_error"] = reason
            self._save_manifest(m)

    # ───────── eylemler ─────────
    def evolve_action(self, arg: str) -> str:
        arg = (arg or "").strip()
        if len(arg) < 8:
            return "Ne eklememi istediğini biraz daha açık söyle."
        if self._busy:
            return "Şu an başka bir özellik üzerinde çalışıyorum."
        self._busy = True
        threading.Thread(target=self._generate_bg, args=(arg,), daemon=True).start()
        return "Üzerinde çalışıyorum patron, kod hazır olunca haber veririm."

    def list_action(self, _: str = "") -> str:
        m = self._manifest()
        if not m:
            return "Henüz eklenti yok."
        rows = []
        for n, i in m.items():
            state = "açık" if i.get("enabled", True) and n in self.loaded else "kapalı"
            rows.append(f"{n} [{state}]: {', '.join(i.get('commands', []))} — {i.get('description', '')}")
        return "\n".join(rows)

    def show_action(self, arg: str) -> str:
        p = PLUGIN_DIR / f"{re.sub(r'[^a-z0-9_]', '', arg.strip().lower())}.py"
        return p.read_text(encoding="utf-8")[:4000] if p.exists() else "Böyle bir eklenti yok."

    def remove_action(self, arg: str) -> str:
        name = re.sub(r"[^a-z0-9_]", "", arg.strip().lower())
        m = self._manifest()
        if name not in m:
            return "Böyle bir eklenti yok."
        self.disable(name, "kullanıcı kaldırdı")
        src = PLUGIN_DIR / f"{name}.py"
        if src.exists():
            shutil.move(str(src), str(REMOVED_DIR / f"{name}_{int(time.time())}.py"))
        m = self._manifest()
        m.pop(name, None)
        self._save_manifest(m)
        return f"'{name}' kaldırıldı (kopyası plugins/_removed içinde)."

    # ───────── üretim ─────────
    def _generate_bg(self, request: str) -> None:
        try:
            result = self.generate(request)
            if result is None:
                return
            name, v, path = result
            self.brain.set_pending(self._question(name, v, path), lambda: self.install(name, v, path, request))
            self.brain.notify(self._question(name, v, path))
        except Exception as e:
            log.exception("EVOLVE hatası")
            self.brain.notify(f"Özelliği yazarken hata oluştu: {e}")
        finally:
            self._busy = False

    def generate(self, request: str, max_attempts: int = 3):
        existing = set(self.reg.names())
        msgs = [{"role": "system", "content": SPEC.format(existing=", ".join(sorted(existing)))},
                {"role": "user", "content": request}]
        v, code = None, ""
        for attempt in range(max_attempts):
            raw = self.brain.complete(msgs, code=True)
            code = extract_code(raw)
            v = validate(code, existing)
            if not v.errors:
                break
            log.info("EVOLVE deneme %d hatalı: %s", attempt + 1, v.errors)
            msgs += [{"role": "assistant", "content": raw},
                     {"role": "user", "content": "Kod şu nedenlerle reddedildi:\n- " + "\n- ".join(v.errors)
                      + "\nKuralları koruyarak düzeltilmiş TAM dosyayı ```python bloğunda tekrar ver."}]
        if v.errors:
            self.brain.notify("Özelliği kurallara uygun yazamadım: " + "; ".join(v.errors[:2]))
            return None
        name = re.sub(r"[^a-z0-9_]", "", v.commands[0].lower()) or f"plugin_{int(time.time())}"
        if name in self._manifest():
            name = f"{name}_{int(time.time()) % 10000}"
        PENDING_DIR.mkdir(parents=True, exist_ok=True)
        path = PENDING_DIR / f"{name}.py"
        path.write_text(code, encoding="utf-8")
        return name, v, path

    @staticmethod
    def _question(name: str, v: Validation, path) -> str:
        bits = [f"'{name}' eklentisi hazır: {', '.join(v.commands)} komutlarını ekler"]
        if v.doc:
            bits.append(v.doc)
        if v.requirements:
            bits.append("kurulacak paketler: " + ", ".join(v.requirements))
        if v.flags:
            bits.append("dikkat, şunları kullanıyor: " + ", ".join(v.flags) + " (bu yüzden komutları hep onay isteyecek)")
        return ". ".join(bits) + f". Kod: {path}. Kurayım mı?"

    def install(self, name: str, v: Validation, path, request: str = "") -> str:
        if v.requirements and not is_online():
            q = PLUGIN_DIR / "_queue.json"
            items = json.loads(q.read_text(encoding="utf-8")) if q.exists() else []
            items.append({"name": name, "path": str(path), "requirements": v.requirements, "request": request})
            atomic_write_json(q, items)
            # Arka planda internet bekleme thread'i başlat (tek sefer)
            threading.Thread(target=self._drain_queue_when_online, daemon=True).start()
            return "İnternet yok, eklenti kuyruğa alındı. İnternet gelince otomatik kurulacak, haber veririm."
        threading.Thread(target=self._install_bg, args=(name, v, path, request), daemon=True).start()
        return "Kuruluma başladım, bitince haber veririm."

    def _drain_queue_when_online(self) -> None:
        """İnternet bağlantısı gelene kadar bekler, sonra kuyruktaki eklentileri kurar."""
        while not is_online():
            time.sleep(15)
        q = PLUGIN_DIR / "_queue.json"
        if not q.exists():
            return
        try:
            items = json.loads(q.read_text(encoding="utf-8"))
        except Exception:
            return
        if not items:
            return
        q.unlink(missing_ok=True)
        self.brain.notify(f"İnternet bağlandı, {len(items)} bekleyen eklenti kuruluyor...")
        for item in items:
            try:
                import pathlib
                name = item["name"]
                path = pathlib.Path(item["path"])
                if not path.exists():
                    self.brain.notify(f"'{name}' için bekleyen dosya bulunamadı, atlanıyor.")
                    continue
                # v nesnesini yeniden oluştur
                code = path.read_text(encoding="utf-8")
                v = validate(code, set(self.reg.names()))
                v.requirements = item.get("requirements", v.requirements)
                threading.Thread(target=self._install_bg,
                                 args=(name, v, path, item.get("request", "")),
                                 daemon=True).start()
            except Exception as e:
                log.exception("Kuyruk kurulum hatası")
                self.brain.notify(f"'{item.get('name', '?')}' kuyruğu işlenirken hata: {e}")


    def _install_bg(self, name: str, v: Validation, path, request: str) -> None:
        try:
            if v.requirements:
                p = subprocess.run([python_exe(), "-m", "pip", "install", "--disable-pip-version-check", "--no-input",
                                    *v.requirements], capture_output=True, text=True, timeout=900,
                                   creationflags=0x08000000 if IS_WIN else 0)
                if p.returncode != 0:
                    raise RuntimeError("pip kurulumu başarısız: " + (p.stderr or p.stdout)[-300:])
                importlib.invalidate_caches()
            ok, info = self.smoke_test(path)
            if not ok:
                raise RuntimeError("duman testi geçmedi: " + info)
            final = PLUGIN_DIR / f"{name}.py"
            shutil.move(str(path), str(final))
            self._load_file(name, final, v.flags)
            m = self._manifest()
            m[name] = {"description": v.doc, "commands": v.commands, "requirements": v.requirements,
                       "flags": v.flags, "enabled": True, "created": int(time.time()), "sha256": sha256(final),
                       "request": request[:300]}
            self._save_manifest(m)
            self.brain.notify(f"Hazır patron: {', '.join(v.commands)} komutu artık kullanılabilir.")
        except Exception as e:
            log.exception("Kurulum hatası")
            self.brain.notify(f"'{name}' kurulamadı: {e}")

    @staticmethod
    def smoke_test(path, timeout: int = 40):
        try:
            p = subprocess.run([python_exe(), "-c", SMOKE, str(path)], capture_output=True, text=True,
                               timeout=timeout, cwd=str(PLUGIN_DIR), creationflags=0x08000000 if IS_WIN else 0)
        except subprocess.TimeoutExpired:
            return False, "zaman aşımı"
        out = (p.stdout or "").strip().splitlines()
        if p.returncode == 0 and out and out[-1].startswith("SMOKE_OK"):
            return True, out[-1]
        return False, (p.stderr or p.stdout or "bilinmeyen hata").strip()[-400:]
