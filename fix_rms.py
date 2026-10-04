import os

path = r"D:\ultron\senses\background_ear.py"
with open(path, "r", encoding="utf-8") as f:
    code = f.read()

old_cb = """    def _audio_callback(self, indata, frames, time_info, status):
        if self.running:
            vol = np.linalg.norm(indata) * 10
            if self.volume_callback:
                self.volume_callback(min(vol * 4, 100.0))
            self.q.put(bytes(indata))"""

new_cb = """    def _audio_callback(self, indata, frames, time_info, status):
        if self.running:
            import numpy as np
            audio_data = np.frombuffer(indata, dtype=np.int16).astype(np.float32)
            rms = np.sqrt(np.mean(audio_data**2))
            # rms genelde sessizlikte 0-50, konusurken 500-10000 arasi olur.
            # 0.0 ile 100.0 arasina normalize edelim:
            vol = min(rms / 40.0, 100.0)
            
            if self.volume_callback:
                self.volume_callback(vol)
            self.q.put(bytes(indata))"""

code = code.replace(old_cb, new_cb)
with open(path, "w", encoding="utf-8") as f:
    f.write(code)
print("Ses volume hesaplamasi duzeltildi!")
