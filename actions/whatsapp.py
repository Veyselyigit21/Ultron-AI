"""WhatsApp Web üzerinden mesaj (arayüz otomasyonu)."""
import time
import webbrowser

from actions import builtin


def send_message(arg: str) -> str:
    contact, _, message = arg.partition("|")
    contact, message = contact.strip(), message.strip()
    if not contact or not message:
        return "Biçim: WHATSAPP: kişi | mesaj"
    pg = builtin._pyautogui()
    webbrowser.open("https://web.whatsapp.com/")
    time.sleep(10)                       # sayfa/QR için bekle
    pg.hotkey("ctrl", "alt", "/")        # arama kutusu
    time.sleep(1)
    builtin.type_text(contact)           # Türkçe karakter güvenli
    time.sleep(2)
    pg.press("enter")
    time.sleep(2)
    builtin.type_text(message)
    time.sleep(0.5)
    pg.press("enter")
    return f"{contact} kişisine mesaj gönderildi (WhatsApp Web açık ve giriş yapılmış olmalı)."


def register(reg) -> None:
    reg.add("WHATSAPP", send_message, "WhatsApp Web'den mesaj gönderir", "WHATSAPP: kişi | mesaj", danger="confirm")
