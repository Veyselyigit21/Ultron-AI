path = r"D:\ultron\main_gui.py"
with open(path, "r", encoding="utf-8") as f:
    code = f.read()

old_cb = """    def on_voice_command_detected(self, text):
        self.wakeup_ui.emit()
        if text and text != "Efendim patron?":
            self.voice_input_received.emit(text)
            t = threading.Thread(target=self._ask_llm, args=(text,), daemon=True)
            t.start()
        else:
            self.ear.resume(as_conversation=True)"""
            
new_cb = """    def on_voice_command_detected(self, text):
        self.wakeup_ui.emit()
        if text and text != "Efendim patron?":
            self.voice_input_received.emit(text)
            t = threading.Thread(target=self._ask_llm, args=(text,), daemon=True)
            t.start()
        else:
            def ack():
                self.backend.mouth.speak("Dinliyorum patron.")
                self.ear.resume(as_conversation=True)
            threading.Thread(target=ack, daemon=True).start()"""

code = code.replace(old_cb, new_cb)

with open(path, "w", encoding="utf-8") as f:
    f.write(code)
print("Callback restored!")
