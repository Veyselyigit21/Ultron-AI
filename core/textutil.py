"""Türkçe-duyarlı metin yardımcıları."""
import re

_TR_UPPER = str.maketrans({"İ": "i", "I": "ı"})
_FOLD = str.maketrans("çğıöşüâîû", "cgiosuaiu")


def tr_lower(s: str) -> str:
    """Python'un 'İ'.lower() hatasını (i + birleşik nokta) önler."""
    return s.translate(_TR_UPPER).lower()


def fold(s: str) -> str:
    """Küçük harf + Türkçe karakterleri ASCII'ye indirger (eşleştirme için)."""
    return tr_lower(s).translate(_FOLD)


def words(s: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", fold(s))


_YES = {"evet", "tamam", "onay", "onayla", "onayliyorum", "yap", "devam", "olur", "kabul", "aynen", "tabii", "tabi"}
_NO = {"hayir", "iptal", "vazgec", "yapma", "dur", "olmaz", "istemiyorum", "degil"}


def parse_yes_no(text: str):
    """True=evet, False=hayır, None=belirsiz. İlk anlamlı kelime belirler."""
    for w in words(text)[:3]:
        if w in _YES:
            return True
        if w in _NO:
            return False
    return None


def split_cmd_tags(text: str):
    """[CMD: AD: arg] etiketlerini bulur (iç içe [] destekler).

    Döner: [(start, end, NAME, arg), ...]
    """
    out, i = [], 0
    while True:
        s = text.find("[CMD", i)
        if s < 0:
            break
        j, depth = s, 0
        while j < len(text):
            c = text[j]
            if c == "[":
                depth += 1
            elif c == "]":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        if j >= len(text):  # kapanmamış etiket: kalanını al
            inner, e = text[s + 4:], len(text)
        else:
            inner, e = text[s + 4:j], j + 1
        inner = inner.lstrip()
        if inner.startswith(":"):
            inner = inner[1:]
        name, _, arg = inner.partition(":")
        name = name.strip().upper()
        if re.fullmatch(r"[A-Z][A-Z0-9_]{1,31}", name):
            out.append((s, e, name, arg.strip()))
        i = e
    return out


def strip_cmd_tags(text: str) -> str:
    tags = split_cmd_tags(text)
    for s, e, _, _ in reversed(tags):
        text = text[:s] + text[e:]
    return re.sub(r"[ \t]{2,}", " ", text).strip()


_EMOJI = re.compile("[\U0001F000-\U0001FFFF\u2600-\u27BF\uFE0F]")


def speech_clean(text: str) -> str:
    """Sesli okunmaya uygun hale getirir."""
    t = strip_cmd_tags(text)
    t = re.sub(r"https?://\S+", "bağlantı", t)
    t = re.sub(r"[`*_#~>|]+", " ", t)
    t = _EMOJI.sub("", t)
    return re.sub(r"\s+", " ", t).strip()


def split_sentences(text: str, max_len: int = 220) -> list[str]:
    """TTS gecikmesini düşürmek için cümlelere böler; kısaları birleştirir."""
    parts = re.split(r"(?<=[.!?…])\s+|\n+", text.strip())
    chunks, cur = [], ""
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if cur and len(cur) + len(p) + 1 > max_len:
            chunks.append(cur)
            cur = p
        elif cur and len(cur) < 25:
            cur = cur + " " + p
        else:
            if cur:
                chunks.append(cur)
            cur = p
    if cur:
        chunks.append(cur)
    out = []
    for c in chunks:  # çok uzun tek cümleyi kelime sınırından kes
        while len(c) > max_len:
            k = c.rfind(" ", 0, max_len)
            k = k if k > 40 else max_len
            out.append(c[:k].strip())
            c = c[k:].strip()
        if c:
            out.append(c)
    return out
