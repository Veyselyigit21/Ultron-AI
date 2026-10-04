import os

path = r"D:\ultron\senses\background_ear.py"
with open(path, "r", encoding="utf-8") as f:
    code = f.read()

# __init__'e ekle
code = code.replace("self.q = queue.Queue()", "self.q = queue.Queue()\n        self.woke_in_this_utterance = False")

# is_final kisminda kontrol ekle
old_final = """                if is_final:
                    result = json.loads(rec.Result())
                    text = result.get('text', '').lower().strip()
                    if not text:
                        continue
                    # Konusma modundaysa ve duraklatilmamissa komutu isle
                    if self.conversation_mode and not self.paused:
                        command = text
                        for w in WAKE_WORDS:
                            command = command.replace(w, '')
                        command = command.strip(' ,.')
                        if command:
                            self.pause()
                            self.callback(command)"""

new_final = """                if is_final:
                    result = json.loads(rec.Result())
                    text = result.get('text', '').lower().strip()
                    
                    # Sonucta wake word var mi?
                    words = text.split()
                    has_wake = any(w in words or text.startswith(w) for w in WAKE_WORDS)
                    
                    # Eger bu cumlede hic uyanilmadiysa ve metinde de ultron yoksa reddet!
                    if not self.woke_in_this_utterance and not has_wake:
                        self.woke_in_this_utterance = False
                        continue
                        
                    self.woke_in_this_utterance = False # Sifirla
                    
                    if not text:
                        continue
                    # Duraklatilmamissa komutu isle (conversation_mode'a gerek yok artik cunku wake word zorunlu)
                    if not self.paused:
                        command = text
                        for w in WAKE_WORDS:
                            command = command.replace(w, '')
                        command = command.strip(' ,.')
                        if command:
                            self.pause()
                            self.callback(command)"""

code = code.replace(old_final, new_final)

# partial kisminda self.woke_in_this_utterance = True yap
old_partial = """                        self.last_wake_time = now
                        self.conversation_mode = True
                        self.last_conversation_time = now"""
                        
new_partial = """                        self.last_wake_time = now
                        self.conversation_mode = True
                        self.last_conversation_time = now
                        self.woke_in_this_utterance = True"""

code = code.replace(old_partial, new_partial)

with open(path, "w", encoding="utf-8") as f:
    f.write(code)
print("background_ear guncellendi")
