"""Yerleşik eylemler: uygulama, dosya, shell, klavye/fare, ses, güç, web...

Windows önceliklidir ama modül Linux/macOS'ta da import edilebilir (testler için);
platforma bağlı kütüphaneler fonksiyon içinde, tembel yüklenir.
"""
from __future__ import annotations

import base64
import difflib
import html as _html
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.parse
import webbrowser
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

import requests

from core.config import IS_WIN, SHOT_DIR, python_exe, settings
from core.safety import is_catastrophic, protected_reason
from core.textutil import fold

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ULTRON/3.0"}
NOWIN = 0x08000000 if IS_WIN else 0  # CREATE_NO_WINDOW
MAX_OUT = 3000


def _cut(s: str, n: int = MAX_OUT) -> str:
    s = (s or "").strip()
    return s if len(s) <= n else s[:n] + f"\n...[{len(s) - n} karakter kısaltıldı]"


# ───────────────────────── uygulama / web ─────────────────────────
APP_ALIASES = {
    "not defteri": "notepad.exe", "notepad": "notepad.exe",
    "hesap makinesi": "calc.exe", "hesap makinasi": "calc.exe", "calculator": "calc.exe",
    "paint": "mspaint.exe", "komut istemi": "cmd.exe", "cmd": "cmd.exe",
    "powershell": "powershell.exe", "terminal": "wt.exe",
    "gorev yoneticisi": "taskmgr.exe", "task manager": "taskmgr.exe",
    "dosya gezgini": "explorer.exe", "explorer": "explorer.exe",
    "ayarlar": "ms-settings:", "denetim masasi": "control.exe",
    "chrome": "chrome", "google chrome": "chrome", "edge": "msedge", "firefox": "firefox",
    "spotify": "spotify", "discord": "discord", "steam": "steam",
    "vscode": "code", "visual studio code": "code",
    "word": "winword", "excel": "excel", "powerpoint": "powerpnt",
}


def _start_menu_lookup(name: str):
    dirs = [os.path.join(os.environ.get("ProgramData", ""), r"Microsoft\Windows\Start Menu\Programs"),
            os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs")]
    found = {}
    for d in dirs:
        for root, _, files in os.walk(d):
            for f in files:
                if f.lower().endswith(".lnk"):
                    found[fold(f[:-4])] = os.path.join(root, f)
    key = fold(name)
    if key in found:
        return found[key]
    sub = [k for k in found if key in k]
    if sub:
        return found[min(sub, key=len)]
    close = difflib.get_close_matches(key, list(found), n=1, cutoff=0.7)
    return found[close[0]] if close else None


def open_app(arg: str) -> str:
    name = arg.strip().strip("\"'")
    if not name:
        return "Hangi uygulama?"
    if re.match(r"^(https?://|www\.)", name, re.I):
        return open_url(name)
    key = fold(name)
    target = APP_ALIASES.get(key, name)
    try:
        if os.path.exists(os.path.expandvars(target)):
            os.startfile(os.path.expandvars(target)) if IS_WIN else subprocess.Popen(["xdg-open", target])
            return f"{name} açıldı."
        if IS_WIN:
            try:
                os.startfile(target)  # App Paths / PATH / URI şemaları
                return f"{name} açıldı."
            except OSError:
                pass
            lnk = _start_menu_lookup(name)
            if lnk:
                os.startfile(lnk)
                return f"{name} açıldı."
            subprocess.Popen(["cmd", "/c", "start", "", target], creationflags=NOWIN)
            return f"{name} için başlatma denendi."
        exe = shutil.which(target)
        if exe:
            subprocess.Popen([exe])
            return f"{name} açıldı."
    except Exception as e:
        return f"{name} açılamadı: {e}"
    return f"{name} uygulamasını bulamadım."


def open_url(arg: str) -> str:
    url = arg.strip()
    if not re.match(r"^https?://", url, re.I):
        url = "https://" + url
    webbrowser.open(url)
    return f"{url} açıldı."


def google(arg: str) -> str:
    webbrowser.open("https://www.google.com/search?q=" + urllib.parse.quote_plus(arg))
    return f"Google'da '{arg}' aranıyor."


def youtube(arg: str) -> str:
    webbrowser.open("https://www.youtube.com/results?search_query=" + urllib.parse.quote_plus(arg))
    return f"YouTube'da '{arg}' aranıyor."


def youtube_play(arg: str) -> str:
    q = urllib.parse.quote_plus(arg)
    try:
        r = requests.get(f"https://www.youtube.com/results?search_query={q}", headers=UA, timeout=8,
                         cookies={"CONSENT": "YES+1"})
        ids = re.findall(r'"videoId":"([\w-]{11})"', r.text)
        if ids:
            webbrowser.open(f"https://www.youtube.com/watch?v={ids[0]}")
            return f"'{arg}' için ilk video oynatılıyor."
    except Exception:
        pass
    webbrowser.open(f"https://www.youtube.com/results?search_query={q}")
    return f"'{arg}' arandı, otomatik oynatma olmadı."


def _html_to_text(h: str) -> str:
    h = re.sub(r"(?is)<(script|style|noscript|svg|head).*?</\1>", " ", h)
    h = re.sub(r"(?s)<[^>]+>", " ", h)
    return re.sub(r"\s+", " ", _html.unescape(h)).strip()


def web_fetch(arg: str) -> str:
    url = arg.strip()
    if not re.match(r"^https?://", url, re.I):
        return "Sadece http/https adresleri açılır."
    r = requests.get(url, headers=UA, timeout=12)
    ct = r.headers.get("content-type", "")
    text = _html_to_text(r.text) if "html" in ct else r.text
    return _cut(text, 4000)


def web_search(arg: str) -> str:
    r = requests.post("https://html.duckduckgo.com/html/", data={"q": arg}, headers=UA, timeout=12)
    out = []
    for m in re.finditer(r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>.*?class="result__snippet"[^>]*>(.*?)</a>',
                         r.text, re.S):
        href, title, snip = m.groups()
        q = urllib.parse.parse_qs(urllib.parse.urlparse(href).query).get("uddg")
        href = q[0] if q else href
        out.append(f"{_html_to_text(title)} — {href}\n   {_html_to_text(snip)}")
        if len(out) >= 5:
            break
    return "\n".join(out) if out else "Arama sonucu alınamadı."


NEWS_FEEDS = ["https://feeds.bbci.co.uk/turkce/rss.xml", "https://www.aa.com.tr/tr/rss/default?cat=guncel",
              "https://feeds.bbcturkce.com/bbcturkce"]


def news(_: str = "") -> str:
    for url in NEWS_FEEDS:
        try:
            r = requests.get(url, headers=UA, timeout=6)
            root = ET.fromstring(r.content)
            titles = [i.findtext("title") for i in root.findall(".//item")[:5] if i.findtext("title")]
            if titles:
                return "Güncel başlıklar: " + " | ".join(t.strip() for t in titles)
        except Exception:
            continue
    return "Haber kaynaklarına şu an ulaşamıyorum."


_WMO = {0: "açık", 1: "çoğunlukla açık", 2: "parçalı bulutlu", 3: "kapalı", 45: "sisli", 48: "sisli",
        51: "hafif çiseleme", 53: "çiseleme", 55: "yoğun çiseleme", 61: "hafif yağmurlu", 63: "yağmurlu",
        65: "şiddetli yağmurlu", 71: "hafif karlı", 73: "karlı", 75: "yoğun karlı", 80: "sağanak", 81: "sağanak",
        82: "şiddetli sağanak", 95: "fırtınalı", 96: "dolulu fırtına", 99: "dolulu fırtına"}


def _ip_city() -> str:
    try:
        d = requests.get("http://ip-api.com/json/?fields=status,city", timeout=5).json()
        return d.get("city", "") if d.get("status") == "success" else ""
    except Exception:
        return ""


def weather(arg: str) -> str:
    city = (arg or "").strip() or settings["home_city"] or _ip_city()
    if not city:
        return "Şehir belirleyemedim, hangi şehir?"
    g = requests.get("https://geocoding-api.open-meteo.com/v1/search",
                     params={"name": city, "count": 1, "language": "tr", "format": "json"}, timeout=8).json()
    if not g.get("results"):
        return f"{city} diye bir yer bulamadım."
    p = g["results"][0]
    w = requests.get("https://api.open-meteo.com/v1/forecast", params={
        "latitude": p["latitude"], "longitude": p["longitude"], "timezone": "auto",
        "current": "temperature_2m,apparent_temperature,weather_code,wind_speed_10m"}, timeout=8).json()["current"]
    desc = _WMO.get(w.get("weather_code"), "")
    return (f"{p['name']} için hava {desc}, {round(w['temperature_2m'])} derece "
            f"(hissedilen {round(w['apparent_temperature'])}), rüzgar {round(w['wind_speed_10m'])} km/s.")


def location(_: str = "") -> str:
    d = requests.get("http://ip-api.com/json/?fields=status,country,city,lat,lon,isp", timeout=6).json()
    if d.get("status") != "success":
        return "Konum alınamadı."
    return f"IP'ye göre yaklaşık konum: {d['city']}, {d['country']} ({d['lat']}, {d['lon']}), ISS: {d['isp']}."


def time_now(_: str = "") -> str:
    n = datetime.now()
    gun = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"][n.weekday()]
    ay = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"][n.month - 1]
    return f"Saat {n:%H:%M}, {n.day} {ay} {n.year} {gun}."


# ───────────────────────── sistem ─────────────────────────
def stats(_: str = "") -> str:
    import psutil
    parts = [f"CPU %{psutil.cpu_percent(interval=0.5):.0f}", f"RAM %{psutil.virtual_memory().percent:.0f}"]
    try:
        parts.append(f"Disk %{psutil.disk_usage(os.path.abspath(os.sep)).percent:.0f}")
        b = psutil.sensors_battery()
        if b:
            parts.append(f"Pil %{b.percent:.0f}{' (şarjda)' if b.power_plugged else ''}")
    except Exception:
        pass
    return ", ".join(parts) + "."


def _pyautogui():
    import pyautogui
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.05
    return pyautogui


def volume(arg: str) -> str:
    a = fold(arg).strip()
    try:
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        from comtypes import CLSCTX_ALL
        from ctypes import POINTER, cast
        dev = AudioUtilities.GetSpeakers()
        ep = getattr(dev, "EndpointVolume", None)  # yeni pycaw
        if ep is None:                              # eski pycaw
            ep = cast(dev.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None), POINTER(IAudioEndpointVolume))
        cur = ep.GetMasterVolumeLevelScalar()
        if a in ("sessiz", "mute", "kapat"):
            ep.SetMute(1, None)
            return "Ses kapatıldı."
        if a in ("ac", "unmute", "sesi ac"):
            ep.SetMute(0, None)
            return "Ses açıldı."
        m = re.search(r"([+-]?)(\d+)", a)
        if not m:
            return f"Ses şu an %{round(cur * 100)}."
        v = int(m.group(2)) / 100
        new = cur + (v if m.group(1) == "+" else -v) if m.group(1) else v
        new = max(0.0, min(1.0, new))
        ep.SetMute(0, None)
        ep.SetMasterVolumeLevelScalar(new, None)
        return f"Ses %{round(new * 100)}."
    except Exception as e:
        try:  # yedek: medya tuşları
            pg = _pyautogui()
            up = "+" in a or "art" in a or "yuksel" in a
            for _ in range(5):
                pg.press("volumeup" if up else "volumedown")
            return "Ses ayarlandı (yedek yöntem)."
        except Exception:
            return f"Ses ayarlanamadı: {e}"


def media(arg: str) -> str:
    key = {"PLAYPAUSE": "playpause", "NEXT": "nexttrack", "PREV": "prevtrack", "STOP": "stop", "MUTE": "volumemute"}
    k = key.get(arg.strip().upper().replace(" ", "").replace("_", ""), "playpause")
    _pyautogui().press(k)
    return "Medya komutu gönderildi."


def lock(_: str = "") -> str:
    if IS_WIN:
        subprocess.Popen(["rundll32.exe", "user32.dll,LockWorkStation"], creationflags=NOWIN)
        return "Ekran kilitlendi."
    return "Kilitleme sadece Windows'ta destekleniyor."


def power(arg: str) -> str:
    a = fold(arg).strip()
    if not IS_WIN:
        return "Güç komutları sadece Windows'ta destekleniyor."
    if a in ("iptal", "cancel", "abort"):
        subprocess.run(["shutdown", "/a"], creationflags=NOWIN)
        return "Kapatma/yeniden başlatma iptal edildi."
    if a in ("kapat", "shutdown", "bilgisayari kapat"):
        subprocess.run(["shutdown", "/s", "/t", "30"], creationflags=NOWIN)
        return "Bilgisayar 30 saniye içinde kapanacak. 'POWER: iptal' ile durdurabilirsin."
    if a in ("yeniden baslat", "restart", "reboot"):
        subprocess.run(["shutdown", "/r", "/t", "30"], creationflags=NOWIN)
        return "30 saniye içinde yeniden başlatılacak."
    if a in ("uyku", "sleep"):
        subprocess.Popen(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"], creationflags=NOWIN)
        return "Uyku moduna geçiliyor."
    return "POWER argümanı: kapat | yeniden baslat | uyku | iptal"


# ───────────────────────── shell / python ─────────────────────────
def _run(cmd_list, timeout, cwd=None) -> str:
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    p = subprocess.run(cmd_list, capture_output=True, timeout=timeout, cwd=cwd or str(Path.home()),
                       stdin=subprocess.DEVNULL, creationflags=NOWIN, env=env)
    out = (p.stdout or b"").decode("utf-8", "replace") + (p.stderr or b"").decode("utf-8", "replace")
    return f"[çıkış kodu {p.returncode}]\n{_cut(out)}"


def shell(arg: str) -> str:
    why = is_catastrophic(arg)
    if why:
        return f"ENGELLENDİ: bu komut ({why}) hiçbir koşulda çalıştırılmaz."
    try:
        if IS_WIN:
            wrapped = f"[Console]::OutputEncoding=[Text.Encoding]::UTF8; {arg}"
            return _run(["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
                         "-Command", wrapped], 60)
        return _run(["bash", "-lc", arg], 60)
    except subprocess.TimeoutExpired:
        return "Komut 60 saniyede bitmedi, durduruldu."


def run_python(arg: str) -> str:
    why = is_catastrophic(arg)
    if why:
        return f"ENGELLENDİ: kod içinde yasaklı desen ({why})."
    try:
        return _run([python_exe(), "-c", arg], 60)
    except subprocess.TimeoutExpired:
        return "Kod 60 saniyede bitmedi, durduruldu."


# ───────────────────────── pano / klavye / fare ─────────────────────────
def _set_clipboard(text: str) -> None:
    b64 = base64.b64encode(text.encode("utf-8")).decode()
    ps = f"Set-Clipboard -Value ([Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('{b64}')))"
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], creationflags=NOWIN, timeout=15)


def clipboard_get(_: str = "") -> str:
    ps = "[Console]::OutputEncoding=[Text.Encoding]::UTF8; Get-Clipboard -Raw"
    p = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, creationflags=NOWIN, timeout=15)
    return _cut(p.stdout.decode("utf-8", "replace"), 3000) or "Pano boş."


def clipboard_set(arg: str) -> str:
    _set_clipboard(arg)
    return "Panoya kopyalandı."


def type_text(arg: str) -> str:
    """Türkçe karakterleri kaybetmemek için panoya koyup Ctrl+V yapar."""
    _set_clipboard(arg)
    time.sleep(0.15)
    _pyautogui().hotkey("ctrl", "v")
    return "Yazıldı."


def hotkey(arg: str) -> str:
    keys = [k.strip().lower() for k in re.split(r"[+,\s]+", arg) if k.strip()]
    if not keys:
        return "Hangi tuşlar?"
    _pyautogui().hotkey(*keys)
    return f"{'+'.join(keys)} basıldı."


def click(arg: str) -> str:
    m = re.findall(r"-?\d+", arg)
    pg = _pyautogui()
    if len(m) >= 2:
        pg.click(int(m[0]), int(m[1]))
        return f"({m[0]}, {m[1]}) konumuna tıklandı."
    pg.click()
    return "Tıklandı."


def screenshot(_: str = "") -> str:
    path = SHOT_DIR / f"ekran_{datetime.now():%Y%m%d_%H%M%S}.png"
    _pyautogui().screenshot().save(path)
    return f"Ekran görüntüsü: {path}"


# ───────────────────────── dosya / süreç ─────────────────────────
def _known_dir(name: str):
    home = Path.home()
    k = fold(name).strip()
    table = {"masaustu": "Desktop", "desktop": "Desktop", "belgelerim": "Documents", "belgeler": "Documents",
             "documents": "Documents", "indirilenler": "Downloads", "downloads": "Downloads",
             "resimler": "Pictures", "muzik": "Music", "videolar": "Videos"}
    if k in table:
        p = home / table[k]
        od = home / "OneDrive" / table[k]
        return od if (not p.exists() and od.exists()) else p
    return None


def _path(p: str) -> Path:
    p = p.strip().strip("\"'")
    kd = _known_dir(p)
    return kd if kd else Path(os.path.expandvars(os.path.expanduser(p)))


def file_list(arg: str) -> str:
    p = _path(arg or "~")
    if not p.is_dir():
        return f"{p} bir klasör değil."
    items = sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
    lines = [("[K] " if i.is_dir() else "    ") + i.name for i in items[:60]]
    more = f"\n... ve {len(items) - 60} öğe daha" if len(items) > 60 else ""
    return f"{p}:\n" + "\n".join(lines) + more


def file_read(arg: str) -> str:
    p = _path(arg)
    if not p.is_file():
        return f"{p} dosyası yok."
    if p.stat().st_size > 2_000_000:
        return "Dosya 2 MB'tan büyük, okunmadı."
    raw = p.read_bytes()
    if b"\x00" in raw[:2048]:
        return "İkili dosya, metin olarak okunamaz."
    for enc in ("utf-8-sig", "cp1254", "latin-1"):
        try:
            return _cut(raw.decode(enc), 6000)
        except UnicodeDecodeError:
            continue
    return "Dosya çözülemedi."


def file_write(arg: str, append: bool = False) -> str:
    path, content = arg.partition("|")[0].strip(), arg.partition("|")[2].lstrip(" ")
    if not path:
        return "Biçim: FILE_WRITE: yol | içerik"
    p = _path(path)
    why = protected_reason(p)
    if why:
        return f"ENGELLENDİ: {p} korumalı ({why})."
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a" if append else "w", encoding="utf-8") as f:
        f.write(content.replace("\\n", "\n"))
    return f"{p} {'eklendi' if append else 'yazıldı'} ({len(content)} karakter)."


def file_append(arg: str) -> str:
    return file_write(arg, append=True)


def file_delete(arg: str) -> str:
    p = _path(arg)
    why = protected_reason(p)
    if why:
        return f"ENGELLENDİ: {p} korumalı ({why})."
    if not p.exists():
        return f"{p} yok."
    try:
        from send2trash import send2trash
    except ImportError:
        return "send2trash kurulu değil; kalıcı silme yapmıyorum. (pip install send2trash)"
    send2trash(str(p))
    return f"{p} geri dönüşüm kutusuna taşındı."


def file_move(arg: str, copy: bool = False) -> str:
    a, b = arg.partition("|")[0].strip(), arg.partition("|")[2].strip()
    if not a or not b:
        return "Biçim: kaynak | hedef"
    src, dst = _path(a), _path(b)
    for p in (dst,) if copy else (src, dst):
        why = protected_reason(p)
        if why:
            return f"ENGELLENDİ: {p} korumalı ({why})."
    if not src.exists():
        return f"{src} yok."
    if copy:
        shutil.copytree(src, dst) if src.is_dir() else shutil.copy2(src, dst)
        return f"{src} → {dst} kopyalandı."
    shutil.move(str(src), str(dst))
    return f"{src} → {dst} taşındı."


def file_copy(arg: str) -> str:
    return file_move(arg, copy=True)


def file_find(arg: str) -> str:
    pat, _, root = arg.partition("|")
    pat = fold(pat.strip())
    base = _path(root.strip() or "~")
    res, scanned = [], 0
    for r, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("node_modules", "__pycache__", "AppData")]
        scanned += 1
        for f in files + dirs:
            if pat in fold(f):
                res.append(os.path.join(r, f))
        if len(res) >= 25 or scanned > 4000:
            break
    return "\n".join(res[:25]) if res else f"'{pat}' bulunamadı ({base})."


def process_list(_: str = "") -> str:
    import psutil
    ps = []
    for p in psutil.process_iter(["pid", "name", "memory_info"]):
        try:
            ps.append((p.info["memory_info"].rss, p.info["name"], p.info["pid"]))
        except Exception:
            continue
    ps.sort(reverse=True)
    return "\n".join(f"{n} (pid {pid}) {rss // 1048576} MB" for rss, n, pid in ps[:10])


_PROTECTED_PROCS = {"system", "csrss.exe", "wininit.exe", "winlogon.exe", "services.exe", "lsass.exe", "smss.exe",
                    "svchost.exe", "dwm.exe", "registry", "init", "systemd"}


def kill(arg: str) -> str:
    import psutil
    a = arg.strip()
    me = {os.getpid(), os.getppid()}
    hit = 0
    for p in psutil.process_iter(["pid", "name"]):
        try:
            n = (p.info["name"] or "").lower()
            match = (a.isdigit() and p.info["pid"] == int(a)) or (not a.isdigit() and n in (a.lower(), a.lower() + ".exe"))
            if not match or p.info["pid"] in me:
                continue
            if n in _PROTECTED_PROCS:
                return f"ENGELLENDİ: {n} kritik bir sistem süreci."
            p.terminate()
            hit += 1
        except Exception:
            continue
    return f"{hit} süreç sonlandırıldı." if hit else f"'{a}' çalışan süreç bulunamadı."


# ───────────────────────── kayıt ─────────────────────────
def register(reg) -> None:
    A = reg.add
    # güvenli
    A("OPEN", open_app, "Uygulama, klasör veya site açar", "OPEN: chrome")
    A("URL", open_url, "Adresi tarayıcıda açar", "URL: example.com")
    A("GOOGLE", google, "Google'da arar (tarayıcıda)", "GOOGLE: sorgu")
    A("YOUTUBE", youtube, "YouTube'da arar", "YOUTUBE: sorgu")
    A("YTPLAY", youtube_play, "YouTube'da ilk videoyu oynatır", "YTPLAY: sorgu")
    A("WEB_SEARCH", web_search, "İnternette arar ve sonuçları sana getirir", "WEB_SEARCH: sorgu", feedback=True, external=True)
    A("WEB_FETCH", web_fetch, "Bir web sayfasının metnini getirir", "WEB_FETCH: https://...", feedback=True, external=True)
    A("HABERLER", news, "Güncel haber başlıklarını okur", "HABERLER")
    A("WEATHER", weather, "Hava durumu (şehir boşsa bulunduğun yer)", "WEATHER: şehir")
    A("LOCATION", location, "IP'ye göre yaklaşık konum", "LOCATION")
    A("TIME", time_now, "Saat ve tarih", "TIME")
    A("STATS", stats, "CPU/RAM/disk/pil durumu", "STATS")
    A("VOLUME", volume, "Ses: 40 | +10 | -10 | sessiz | aç", "VOLUME: 40")
    A("MEDIA", media, "Medya tuşu: PLAYPAUSE | NEXT | PREV | STOP", "MEDIA: PLAYPAUSE")
    A("SCREENSHOT", screenshot, "Ekran görüntüsü alır", "SCREENSHOT")
    A("LOCK", lock, "Ekranı kilitler", "LOCK")
    A("FILE_LIST", file_list, "Klasör içeriğini listeler", "FILE_LIST: masaüstü", feedback=True)
    A("FILE_READ", file_read, "Metin dosyasını okur", "FILE_READ: yol", feedback=True, external=True)
    A("FILE_FIND", file_find, "Dosya/klasör arar", "FILE_FIND: ad | klasör", feedback=True)
    A("PROCESS_LIST", process_list, "En çok bellek kullanan süreçler", "PROCESS_LIST", feedback=True)
    A("CLIPBOARD_GET", clipboard_get, "Panodaki metni getirir", "CLIPBOARD_GET", feedback=True, external=True)
    # onay gerektirenler
    C = {"danger": "confirm"}
    A("SHELL", shell, "PowerShell/bash komutu çalıştırır, çıktıyı getirir", "SHELL: komut", feedback=True, **C)
    A("PYTHON", run_python, "Python kodu çalıştırır, çıktıyı getirir", "PYTHON: kod", feedback=True, **C)
    A("FILE_WRITE", file_write, "Dosya yazar/üzerine yazar", "FILE_WRITE: yol | içerik", **C)
    A("FILE_APPEND", file_append, "Dosyanın sonuna ekler", "FILE_APPEND: yol | içerik", **C)
    A("FILE_DELETE", file_delete, "Dosyayı geri dönüşüm kutusuna atar", "FILE_DELETE: yol", **C)
    A("FILE_MOVE", file_move, "Dosya taşır/yeniden adlandırır", "FILE_MOVE: kaynak | hedef", **C)
    A("FILE_COPY", file_copy, "Dosya kopyalar", "FILE_COPY: kaynak | hedef", **C)
    A("KILL", kill, "Süreç sonlandırır (ad veya pid)", "KILL: notepad", **C)
    A("POWER", power, "kapat | yeniden baslat | uyku | iptal", "POWER: kapat", **C)
    A("TYPE", type_text, "Odaktaki pencereye yazı yazar", "TYPE: metin", **C)
    A("HOTKEY", hotkey, "Tuş kombinasyonu basar", "HOTKEY: ctrl+c", **C)
    A("CLICK", click, "Ekranda tıklar", "CLICK: x, y", **C)
    A("CLIPBOARD_SET", clipboard_set, "Panoya metin koyar", "CLIPBOARD_SET: metin", **C)
