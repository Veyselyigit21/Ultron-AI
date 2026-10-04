import speech_recognition as sr
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import tempfile
import os
import time

class Ear:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.samplerate = 16000

    def listen(self, duration=5):
        try:
            print("[E.D.I.T.H.] 5 saniye dinleniyor...")
            # duration saniye boyunca kayıt al (bloklayarak)
            recording = sd.rec(int(duration * self.samplerate), samplerate=self.samplerate, channels=1, dtype='float32')
            sd.wait() # Kaydın bitmesini bekle
            
            # PCM (int16) formatına dönüştür
            audio_np_int16 = (recording * 32767).astype(np.int16)
            
            temp_wav = tempfile.mktemp(suffix='.wav')
            wav.write(temp_wav, self.samplerate, audio_np_int16)
            
            text = None
            with sr.AudioFile(temp_wav) as source:
                audio = self.recognizer.record(source)
                try:
                    text = self.recognizer.recognize_google(audio, language="tr-TR")
                    print(f"Sen (Sesli): {text}")
                except sr.UnknownValueError:
                    print("Ses anlaşılamadı.")
                except sr.RequestError as e:
                    print(f"İnternet bağlantı hatası: {e}")
                    
            if os.path.exists(temp_wav):
                try: os.remove(temp_wav)
                except: pass
                
            return text
        except Exception as e:
            print(f"Mikrofon hatası: {e}")
            return None

if __name__ == "__main__":
    ear = Ear()
    print(ear.listen())
