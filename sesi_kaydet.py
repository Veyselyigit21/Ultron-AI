import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import os

print("\n--- E.D.I.T.H SES İZİ (VOICEPRINT) KAYIT SİSTEMİ ---")
print("Lütfen 5 saniye boyunca normal bir ses tonuyla konuşun...")
print("Örnek: 'Merhaba E.D.I.T.H, ben patron. Sesimi sisteme kaydet.'")
print("\nKayıt 3 saniye içinde başlıyor...")

import time
time.sleep(3)
print(">>> KAYIT BAŞLADI! KONUŞUN! <<<")

samplerate = 16000
duration = 5.0
audio = sd.rec(int(samplerate * duration), samplerate=samplerate, channels=1, dtype="int16")
sd.wait()

print(">>> KAYIT BİTTİ! <<<")

os.makedirs(r"D:\ultron\assets", exist_ok=True)
wav.write(r"D:\ultron\assets\boss_voice.wav", samplerate, audio)
print("Ses İzi başarıyla 'assets/boss_voice.wav' dosyasına kaydedildi!")
print("E.D.I.T.H artık sadece bu sesi duyduğunda tepki verecek.")
time.sleep(4)

