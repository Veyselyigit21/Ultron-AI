import os

import sys

import time

import json

import queue

import ctypes

import threading

import subprocess

import numpy as np

import sounddevice as sd

import pystray

from PIL import Image, ImageDraw



# Konsol penceresini tamamen gizle

hwnd = ctypes.windll.kernel32.GetConsoleWindow()

if hwnd:

    ctypes.windll.user32.ShowWindow(hwnd, 0)



GUI_PROCESS = None



# â”€â”€ Tray ikonu â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def setup_tray_icon():

    img = Image.new('RGB', (64, 64), (0, 0, 0))

    dc = ImageDraw.Draw(img)

    dc.ellipse((12, 12, 52, 52), fill=(0, 180, 255))

    dc.text((18, 22), "ULTRON", fill=(255, 255, 255))



    def on_quit(icon, item):

        icon.stop()

        os._exit(0)



    def on_show(icon, item):

        with open(r"D:\ultron\wakeup.txt", "w") as f:

            f.write("wake")

        global GUI_PROCESS

        if GUI_PROCESS is None or GUI_PROCESS.poll() is not None:

            python_exe = os.path.join(os.path.dirname(__file__), "venv", "Scripts", "pythonw.exe")

            GUI_PROCESS = subprocess.Popen([python_exe, os.path.join(os.path.dirname(__file__), "main_gui.py")])



    menu = pystray.Menu(

        pystray.MenuItem("ULTRON Arka Plan", lambda: None),

        pystray.MenuItem("Arayüzü Göster", on_show),

        pystray.MenuItem("Çıkış", on_quit),

    )

    icon = pystray.Icon("ultron", img, "ULTRON", menu)

    icon.run()





# â”€â”€ Wake-word Dinleyicisi (Vosk Offline) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def listen_loop():

    global GUI_PROCESS



    # Vosk modeli yÃ¼kle

    try:

        from vosk import Model, KaldiRecognizer

        model_path = os.path.join(os.path.dirname(__file__), "vosk-model-small-tr-0.3")

        if not os.path.exists(model_path):

            # Model henÃ¼z yok â€” indirme tamamlanmamÄ±ÅŸ olabilir, bekle

            with open(r"D:\ultron\daemon_words.log", "a", encoding="utf-8") as f:

                f.write("[HATA] Vosk model klasÃ¶rÃ¼ bulunamadÄ±: " + model_path + "\n")

            return

        model = Model(model_path)

        rec = KaldiRecognizer(model, 16000)
        try:
            MODEL_PATH_EN = os.path.abspath(os.path.join(os.path.dirname(__file__), 'vosk-model-en'))
            model_en = Model(MODEL_PATH_EN)
            rec_en = KaldiRecognizer(model_en, 16000)
            has_en = True
        except Exception as e:
            has_en = False
            print("English model error:", e)

        with open(r"D:\ultron\daemon_words.log", "a", encoding="utf-8") as f:

            f.write("[INFO] Vosk modeli yÃ¼klendi, dinleme baÅŸladÄ±.\n")

    except Exception as e:

        with open(r"D:\ultron\daemon_words.log", "a", encoding="utf-8") as f:

            f.write(f"[HATA] Vosk yÃ¼klenemedi: {e}\n")

        return



    WAKE_WORDS = ["hey ultron", "merhaba ultron", "ultron uyan", "ultron dinle", "ultron açıl", "ultron", "ultra", "ultran", "altron", "oltron", "ultra an", "altran", "akron", "uran", "atron", "otron", "antro", "voltran", "uç rol", "uykusu rol", "uçurol", "uçu rol", "turan", "o çukura", "botu"]

    last_wake_time = 0  # AynÄ± uyandÄ±rmayÄ± iki kez tetiklememek iÃ§in cooldown



    python_exe = os.path.join(os.path.dirname(__file__), "venv", "Scripts", "pythonw.exe")

    gui_path   = os.path.join(os.path.dirname(__file__), "main_gui.py")



    samplerate = 16000

    blocksize  = 4000  # 0.25 saniye â€” daha hÄ±zlÄ± tepki iÃ§in kÃ¼Ã§Ã¼k blok



    def audio_cb(indata, frames, time_info, status):

        q.put(bytes(indata))



    q = queue.Queue()



    with sd.RawInputStream(samplerate=samplerate, blocksize=blocksize,

                           dtype="int16", channels=1, callback=audio_cb):

        with open(r"D:\ultron\daemon_words.log", "a", encoding="utf-8") as f:

            f.write("[INFO] Mikrofon akÄ±ÅŸÄ± aÃ§Ä±ldÄ±.\n")

        while True:

            data = q.get()

            

            is_final = rec.AcceptWaveform(data)
            is_final_en = False
            if has_en:
                is_final_en = rec_en.AcceptWaveform(data)

            if is_final:

                result = json.loads(rec.Result())

                text = result.get("text", "").lower().strip()

            else:

                partial = json.loads(rec.PartialResult())

                text = partial.get("partial", "").lower().strip()



            if not text:

                continue



            words = text.split()
            is_wake = any(word.startswith(w) for word in words for w in WAKE_WORDS)
            
            if not is_wake and has_en:
                if is_final_en:
                    text_en = json.loads(rec_en.Result()).get('text', '').lower().strip()
                else:
                    text_en = json.loads(rec_en.PartialResult()).get('partial', '').lower().strip()

                if text_en and "ultron" not in text_en and "altron" not in text_en:
                    with open("D:/ultron/daemon_words.log", "a", encoding="utf-8") as f:
                        f.write("[EN Duyuldu] " + text_en + "\n")

                if "ultron" in text_en or "altron" in text_en or "ltron" in text_en or "outrun" in text_en or "eltron" in text_en or "old run" in text_en or "all drawn" in text_en:
                    is_wake = True
                    text = text_en



            if is_wake:

                now = time.time()

                if now - last_wake_time < 5.0:  # 5 saniye cooldown â€” Ã§ift tetiklemeyi Ã¶nler

                    continue

                last_wake_time = now

                

                with open(r"D:\ultron\daemon_words.log", "a", encoding="utf-8") as f:

                    f.write(f"[UYANMA] Wake word: {text}\n")



                # Siber uyandÄ±rma sesi

                try:

                    import winsound

                    winsound.PlaySound(r"D:\ultron\assets\wake_cyber.wav",

                                       winsound.SND_FILENAME | winsound.SND_ASYNC)

                except Exception:

                    pass



                # GUI'yi baÅŸlat ve bitiÅŸini bekle

                GUI_PROCESS = subprocess.Popen([python_exe, gui_path])

                GUI_PROCESS.wait()

                time.sleep(1)



                # Kuyrukta biriken eski ses verilerini temizle

                while not q.empty():

                    try:

                        q.get_nowait()

                    except queue.Empty:

                        break



                # Recognizer'Ä± sÄ±fÄ±rla

                rec.Reset()

            elif is_final and text:

                with open(r"D:\ultron\daemon_words.log", "a", encoding="utf-8") as f:

                    f.write(f"[Duyuldu] {text}\n")





if __name__ == "__main__":

    threading.Thread(target=listen_loop, daemon=True).start()

    setup_tray_icon()











