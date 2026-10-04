import json
import os
import queue
import threading
import time
import numpy as np
import sounddevice as sd
from colorama import Fore, Style

MODEL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'vosk-model-small-tr-0.3'))
WAKE_WORDS = ["hey ultron", "merhaba ultron", "ultron uyan", "ultron dinle", "ultron açıl", "ultron", "ultra", "ultran", "altron", "oltron", "ultra an", "altran", "akron", "uran", "atron", "otron", "antro", "voltran", "uç rol", "uykusu rol", "uçurol", "uçu rol", "turan", "o çukura", "botu"]

class BackgroundEar:
    def __init__(self, callback, volume_callback=None, mouth=None):
        self.callback = callback
        self.volume_callback = volume_callback
        self.mouth = mouth
        self.running = False
        self.paused = False
        self.conversation_mode = False
        self.last_conversation_time = 0
        self.last_wake_time = 0
        self.q = queue.Queue()
        self.woke_in_this_utterance = False

    def _audio_callback(self, indata, frames, time_info, status):
        if self.running:
            import numpy as np
            audio_data = np.frombuffer(indata, dtype=np.int16).astype(np.float32)
            rms = np.sqrt(np.mean(audio_data**2))
            vol = min(rms / 40.0, 100.0)
            
            if self.volume_callback:
                self.volume_callback(vol)
            self.q.put(bytes(indata))

    def start_listening(self):
        self.running = True
        threading.Thread(target=self._process_audio, daemon=True).start()

    def stop_listening(self):
        self.running = False

    def pause(self):
        self.paused = True

    def resume(self, as_conversation=True):
        self.paused = False
        while not self.q.empty():
            try: self.q.get_nowait()
            except: break
        if as_conversation:
            self.conversation_mode = True
            self.last_conversation_time = time.time()

    def _process_audio(self):
        try:
            from vosk import Model, KaldiRecognizer
            model = Model(MODEL_PATH)
            rec = KaldiRecognizer(model, 16000)
            
            try:
                MODEL_PATH_EN = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'vosk-model-en'))
                model_en = Model(MODEL_PATH_EN)
                rec_en = KaldiRecognizer(model_en, 16000)
                has_en = True
            except:
                has_en = False
            print(f"{Fore.CYAN}[ULTRON] Vosk STT hazir, dinleme aktif.{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}[ULTRON] Vosk yuklenemedi: {e}{Style.RESET_ALL}")
            return

        with sd.RawInputStream(samplerate=16000, blocksize=4000, dtype='int16',
                               channels=1, callback=self._audio_callback):
            while self.running:
                if self.conversation_mode and time.time() - self.last_conversation_time > 15:
                    self.conversation_mode = False

                try:
                    data = self.q.get(timeout=0.5)
                except queue.Empty:
                    continue

                is_final = rec.AcceptWaveform(data)
                is_final_en = False
                if has_en:
                    is_final_en = rec_en.AcceptWaveform(data)

                # Process English result carefully to not lose it
                text_en = ""
                if has_en:
                    if is_final_en:
                        text_en = json.loads(rec_en.Result()).get('text', '').lower().strip()
                    else:
                        text_en = json.loads(rec_en.PartialResult()).get('partial', '').lower().strip()

                if is_final:
                    result = json.loads(rec.Result())
                    text = result.get('text', '').lower().strip()
                    
                    words = text.split()
                    has_wake = any(w in words or text.startswith(w) for w in WAKE_WORDS)
                    
                    # English model caught it in this utterance?
                    if text_en and any(w in text_en for w in ["ultron", "altron", "ltron", "outrun", "eltron", "old run", "all drawn", "all drawn on", "oh drawn", "oh wrong", "or drawn", "oh it's wrong", "always run", "well drawn", "well from", "what wrong"]):
                        has_wake = True
                        self.woke_in_this_utterance = True

                    if not self.woke_in_this_utterance and not has_wake:
                        self.woke_in_this_utterance = False
                        continue
                        
                    self.woke_in_this_utterance = False
                    
                    if not text:
                        continue
                        
                    if not self.paused:
                        command = text
                        for w in WAKE_WORDS:
                            command = command.replace(w, '')
                        command = command.strip(' ,.')
                        if command:
                            self.pause()
                            self.callback(command)
                else:
                    partial = json.loads(rec.PartialResult())
                    text = partial.get('partial', '').lower().strip()
                    
                    words = text.split()
                    is_wake = any(word.startswith(w) for word in words for w in WAKE_WORDS)
                    
                    if not is_wake and text_en:
                        if any(w in text_en for w in ["ultron", "altron", "ltron", "outrun", "eltron", "old run", "all drawn", "all drawn on", "oh drawn", "oh wrong", "or drawn", "oh it's wrong", "always run", "well drawn", "well from", "what wrong"]):
                            is_wake = True
                            text = text_en

                    if is_wake and not self.paused:
                        now = time.time()
                        if now - self.last_wake_time < 5.0:
                            continue
                        self.last_wake_time = now
                        self.conversation_mode = True
                        self.last_conversation_time = now
                        self.woke_in_this_utterance = True
                        print(f"{Fore.CYAN}[ULTRON] Wake word: {text}{Style.RESET_ALL}")
                        
                        
                        
                        self.pause()
                        self.callback('')
                        rec.Reset()
