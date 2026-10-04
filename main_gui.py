import sys
import psutil

import os

import time

import threading

import re

from PyQt6.QtCore import QUrl, QObject, pyqtSignal, pyqtSlot, QTimer, Qt

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget

from PyQt6.QtWebEngineWidgets import QWebEngineView

from PyQt6.QtWebChannel import QWebChannel



from core.llm_manager import LLMManager

from senses.voice import Mouth

from senses.background_ear import BackgroundEar



# Titreme engelleme - sadece bu bayrak

# Removed unstable GPU flags that cause flickering



from PyQt6.QtWebEngineCore import QWebEnginePage
class CustomWebPage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        with open("D:/ultron/js_console.log", "a", encoding="utf-8") as f:
            f.write(f"[{level}] {message} (Line {lineNumber})\n")
        super().javaScriptConsoleMessage(level, message, lineNumber, sourceID)

class Backend(QObject):

    message_received       = pyqtSignal(str)

    voice_input_received   = pyqtSignal(str)

    voice_state_changed    = pyqtSignal(bool)

    mic_volume_changed     = pyqtSignal(float)

    ultron_speaking_changed = pyqtSignal(bool)

    wakeup_ui              = pyqtSignal()

    hide_ui                = pyqtSignal()



    def __init__(self):

        super().__init__()

        self.llm   = LLMManager(use_local=False, api_model="google/gemini-2.5-flash")

        self.mouth = Mouth()

        self.ear   = BackgroundEar(

            callback=self.on_voice_command_detected,

            volume_callback=self._store_volume,

            mouth=self.mouth

        )

        self._is_listening = False

        self.ear.start_listening()



    def _store_volume(self, vol):

        self.mic_volume_changed.emit(float(vol) / 25.0)

        is_active = float(vol) > 4.0

        if is_active != self._is_listening:

            self._is_listening = is_active

            self.voice_state_changed.emit(is_active)



    def on_voice_command_detected(self, text):

        self.wakeup_ui.emit()

        if text and text != "Efendim patron?":

            self.voice_input_received.emit(text)

            t = threading.Thread(target=self._ask_llm, args=(text,), daemon=True)

            t.start()

        else:

            self.ear.resume(as_conversation=True)



    @pyqtSlot(str)

    def processInput(self, text):

        quit_cmds = ['kapat', 'cikis', 'sistemi kapat', 'exit', 'quit']

        if text.strip().lower() in quit_cmds:

            self.message_received.emit("Sistem kapatılıyor. Görüşmek üzere patron.")

            self.mouth.speak("Sistem kapatılıyor. Görüşmek üzere patron.")

            QApplication.quit()

            return

        t = threading.Thread(target=self._ask_llm, args=(text,), daemon=True)

        t.start()



    def _speak_and_signal(self, text):

        self.ultron_speaking_changed.emit(True)

        try:

            self.mouth.speak(text)

        except Exception as e:

            pass

        self.ultron_speaking_changed.emit(False)



    def _ask_llm(self, text):

        try:

            response = self.llm.ask(text)

        except Exception as e:

            response = f"Bir hata oluştu: {e}"



        spoken = re.sub(r'\[CMD:.*?\]', '', response).strip()

        spoken = re.sub(r'\(\)', '', spoken).strip()



        if "[CMD: GIZLE]" in response:

            self.hide_ui.emit()



        self.message_received.emit(response)



        if spoken:

            threading.Thread(target=self._speak_and_signal, args=(spoken,), daemon=True).start()



        self.ear.resume(as_conversation=True)





class UltronGUI(QMainWindow):

    def __init__(self):

        super().__init__()

        self.setWindowTitle("ULTRON")

        self.setStyleSheet("background-color:#050505;")



        self.browser = QWebEngineView()
        self.custom_page = CustomWebPage(self.browser)
        self.browser.setPage(self.custom_page)

        self.browser.page().setBackgroundColor(Qt.GlobalColor.black)


        html_path = os.path.abspath(

            os.path.join(os.path.dirname(__file__), "gui", "index_v2.html")

        )



        self.channel = QWebChannel()

        self.backend = Backend()

        self.channel.registerObject("backend", self.backend)

        self.browser.page().setWebChannel(self.channel)



        self.backend.message_received.connect(self.send_to_js)

        self.backend.voice_input_received.connect(self.send_voice_to_js)

        self.backend.wakeup_ui.connect(self.wake_window)

        self.backend.hide_ui.connect(self.hide)



        self.browser.setUrl(QUrl.fromLocalFile(html_path))



        # Layout buraya - check_wakeup icinde degil!

        central = QWidget()

        lay = QVBoxLayout(central)

        lay.setContentsMargins(0, 0, 0, 0)

        lay.addWidget(self.browser)

        self.setCentralWidget(central)

        self.showMaximized()



        # Tepsi ikon wakeup timer

        self.wakeup_timer = QTimer()

        self.wakeup_timer.timeout.connect(self.check_wakeup)

        self.wakeup_timer.start(500)



        QTimer.singleShot(800, self.startup_routine)
        
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self.send_real_stats)
        self.stats_timer.start(2000)




    def send_real_stats(self):
        try:
            import psutil
            cpu = int(psutil.cpu_percent())
            ram = int(psutil.virtual_memory().percent)
            gpu = 0
            js = f"if(typeof updateRealStats === 'function') updateRealStats({cpu}, {ram}, {gpu});"
            self.browser.page().runJavaScript(js)
        except Exception as e:
            pass

    def wake_window(self):

        self.showMaximized()

        self.activateWindow()

        



    def check_wakeup(self):

        wakeup_path = r"D:\ultron\wakeup.txt"

        if os.path.exists(wakeup_path):

            try: os.remove(wakeup_path)

            except: pass

            self.showMaximized()

            self.activateWindow()



    def startup_routine(self):

        import datetime

        import random

        now = datetime.datetime.now()

        h = now.hour

        if h < 5:

            greet = "Gece mesaisi mi patron? İyi geceler."

        elif h < 12:

            greet = "Günaydın patron."

        elif h < 18:

            greet = "İyi günler patron."

        elif h < 22:

            greet = "İyi akşamlar patron."

        else:

            greet = "İyi geceler.patron."



        greetings = [

            "Tüm ULTRON protokolleri devrede.",

            "Sistemler aktif ve emrinizdeyim.",

            "Çekirdek sistemler çevrimiçi, dinliyorum.",

            "Arkaplan servisleri kusursuz çalışıyor.",

            "Bağlantı sağlandı, sizi dinliyorum."

        ]

        msg = f"{greet} {random.choice(greetings)} Saat {now.strftime('%H:%M')}."



        

        self.backend.message_received.emit(msg)

        QTimer.singleShot(100, lambda: threading.Thread(

            target=self.backend.mouth.speak, args=(msg,), daemon=True).start())



    def send_to_js(self, text):

        import json

        safe = json.dumps(text)

        self.browser.page().runJavaScript(f'receiveMessage({safe});')

        model_text = "Ollama [OFFLINE]" if self.backend.llm.use_local else "Gemini 2.5 Flash [ONLINE]"

        self.browser.page().runJavaScript(

            f"if(document.getElementById('st-model')) document.getElementById('st-model').textContent = '\u25cf {model_text}';")



    def send_voice_to_js(self, text):

        import json

        safe = json.dumps(text)

        self.browser.page().runJavaScript(f'receiveVoiceInput({safe});')





if __name__ == "__main__":

    app = QApplication(sys.argv)

    window = UltronGUI()

    sys.exit(app.exec())

















