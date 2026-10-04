import os
import subprocess
import pygame
import re
import queue
import threading
import uuid
import time

ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'assets'))

class Mouth:
    def __init__(self):
        pygame.mixer.init()
        self.edge_tts = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'venv', 'Scripts', 'edge-tts.exe'))
        os.makedirs(ASSETS_DIR, exist_ok=True)
        
        self.speaking = False
        self._stop = False
        self.audio_queue = queue.Queue()
        
        # Oynatma iplikcigini baslat
        self.worker = threading.Thread(target=self._play_loop, daemon=True)
        self.worker.start()

    def speak(self, text):
        if not text or not text.strip(): return
        clean_text = re.sub(r'[\(\[].*?[\)\]]', '', text)
        clean_text = clean_text.replace('*', '').strip()
        if not clean_text: return

        unique_id = str(uuid.uuid4())[:8]
        output_file = os.path.join(ASSETS_DIR, f'voice_chunk_{unique_id}.mp3')
        
        try:
            import sys
            result = subprocess.run(
                [sys.executable, '-m', 'edge_tts', '--voice', 'tr-TR-AhmetNeural', '--text', clean_text, '--write-media', output_file],
                capture_output=True, timeout=15, creationflags=subprocess.CREATE_NO_WINDOW
            )
            if result.returncode == 0 and os.path.exists(output_file):
                self.audio_queue.put(output_file)
        except Exception as e:
            with open(r'D:\ultron\voice_error.log', 'a') as f: f.write(f'[TTS Hata]: {e}\n')

    def _play_loop(self):
        while True:
            try:
                # Kuyruktan mp3 dosyasi bekle
                output_file = self.audio_queue.get(block=True, timeout=0.5)
                
                if self._stop:
                    try: os.remove(output_file)
                    except: pass
                    continue
                    
                self.speaking = True
                if not pygame.mixer.get_init():
                    pygame.mixer.init()
                
                try:
                    pygame.mixer.music.load(output_file)
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy():
                        if self._stop:
                            pygame.mixer.music.stop()
                            break
                        pygame.time.Clock().tick(10)
                    pygame.mixer.music.unload()
                except Exception as e:
                    pass
                finally:
                    # Is bitince mp3 dosyasini temizle
                    try: os.remove(output_file)
                    except: pass
                    
            except queue.Empty:
                if self.audio_queue.empty():
                    self.speaking = False
            except Exception:
                pass

    def interrupt(self):
        self._stop = True
        # Kuyruktaki eski dosyalari temizle
        while not self.audio_queue.empty():
            try:
                f = self.audio_queue.get_nowait()
                try: os.remove(f)
                except: pass
            except: break
        
        # Yeniden konusmaya izin ver
        time.sleep(0.1)
        self._stop = False
