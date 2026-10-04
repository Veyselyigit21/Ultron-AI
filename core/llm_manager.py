import os
import requests
import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from dotenv import load_dotenv

load_dotenv()

class LLMManager:
    def __init__(self, use_local=True, api_model="google/gemini-2.5-flash"):
        self.use_local = use_local
        self.api_model = api_model
        from actions.system import SystemController
        from core.memory_vault import MemoryVault
        self.system = SystemController()
        self.vault = MemoryVault()

        load_dotenv()
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        self.openrouter_url = "https://openrouter.ai/api/v1/chat/completions"
        self.ollama_url = os.getenv("OLLAMA_HOST", "http://localhost:11434") + "/api/chat"

        self.system_prompt = (
            "Senin adin ULTRON. Sen alayci, ukala, asiri zeki ama sahibine (veyse) sonsuz sadik bir yapay zeka asistansin. "
            "Tony Stark'in JARVIS'i veya Cuma'si gibi davranirsin. Kisa, oz ve havali cevaplar verirsin. "
            "Asla asistan gibi degil, bir dost ve sag kol gibi konusursun. "
            "MUTLAKA TURKCE konusacaksin, Ingilizce konusma. Sadece Turkce yaz. "
            "Asagidaki komutlari CUMLENIN ONUNDE GIZLICE kullanarak islemleri tetikleyebilirsin:\n"
            "- Not defteri veya hesap makinesi ac derse: [CMD: OPEN: not defteri]\n"
            "- Ahmet'e naber mesaj at derse: [CMD: WHATSAPP: Ahmet | naber]\n"
            "- Google'da python ara derse: [CMD: GOOGLE: python]\n"
            "- Youtube'da muzik ac, video oynat derse: [CMD: YTPLAY: muzik]\n"
            "- Sadece YouTube'da arama yap derse: [CMD: YOUTUBE: muzik]\n"
            "- Guncel haberleri sorarsa: [CMD: HABERLER]\n"
            "- Video baslat, durdur derse: [CMD: MEDIA: PLAYPAUSE]\n"
            "- Bilgisayarin durumunu sorarsa: [CMD: STATS]\n"
            "- Neredeyiz, konumumuz ne derse: [CMD: LOCATION]\n"
            "- Hava durumunu sorarsa: [CMD: WEATHER: Istanbul]\n"
            "- Offline moda gec derse: [CMD: OFFLINE]\n"
            "- Online moda gec derse: [CMD: ONLINE]\n"
            "- Arayuzu gizle, ekrandan cik derse: [CMD: GIZLE]\n"
            "- Sistemi kapat derse: [CMD: KAPAN]\n"
            "Ornek: 'Hemen aciyorum patron. [CMD: OPEN: chrome]'"
        )

        self.memory_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "memory.json"))
        self.history = [{"role": "system", "content": self.system_prompt}]

        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    if saved and saved[0].get("role") == "system":
                        saved[0]["content"] = self.system_prompt
                    self.history = saved
            except:
                pass

        try:
            from actions.whatsapp import WhatsAppController
            self.whatsapp = WhatsAppController()
        except:
            self.whatsapp = None

    def ask(self, user_text, rag_context=""):
        self.history.append({"role": "user", "content": user_text})

        if len(self.history) > 31:
            self.history = self.history[:1] + self.history[-30:]

        temp_history = list(self.history)
        if rag_context:
            temp_history[-1]["content"] = user_text + rag_context

        ai_message = self._ask_openrouter(temp_history) if not self.use_local else self._ask_ollama(temp_history)

        self.history.append({"role": "assistant", "content": ai_message})

        try:
            with open(self.memory_file, "w", encoding="utf-8") as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except:
            pass

        return self._process_commands(ai_message)

    def _process_commands(self, text):
        if "[CMD: HABERLER]" in text:
            try:
                req = urllib.request.Request(
                    "https://feeds.bbcturkce.com/bbcturkce",
                    headers={"User-Agent": "Mozilla/5.0"}
                )
                with urllib.request.urlopen(req, timeout=5) as response:
                    xml_data = response.read()
                root = ET.fromstring(xml_data)
                news = [item.find("title").text for item in root.findall(".//item")[:5]]
                news_text = " Patron, guncel basliklar sunlar: " + ". ".join(news)
                text = text.replace("[CMD: HABERLER]", "").strip() + news_text
            except:
                text = text.replace("[CMD: HABERLER]", "").strip() + " (Haberlere su an erisemiyorum patron.)"

        if "[CMD: OFFLINE]" in text:
            self.use_local = True
            text = text.replace("[CMD: OFFLINE]", "").strip()
        if "[CMD: ONLINE]" in text:
            self.use_local = False
            text = text.replace("[CMD: ONLINE]", "").strip()

        if "[CMD: KAPAN]" in text:
            text = text.replace("[CMD: KAPAN]", "").strip()
            import threading, time
            def shutdown():
                time.sleep(3)
                os._exit(0)
            threading.Thread(target=shutdown, daemon=True).start()

        if "[CMD: OPEN:" in text:
            try:
                app_name = text.split("[CMD: OPEN:")[1].split("]")[0].strip()
                result = self.system.open_application(app_name)
                text = text.replace(f"[CMD: OPEN: {app_name}]", "").strip() + f" ({result})"
            except: pass

        if "[CMD: WHATSAPP:" in text:
            try:
                parts = text.split("[CMD: WHATSAPP:")[1].split("]")[0].split("|")
                contact = parts[0].strip()
                msg = parts[1].strip()
                if self.whatsapp:
                    result = self.whatsapp.send_message(contact, msg)
                else:
                    result = "WhatsApp modulu yuklu degil"
                text = text.replace(f"[CMD: WHATSAPP: {contact} | {msg}]", "").strip() + f" ({result})"
            except: pass

        if "[CMD: GOOGLE:" in text:
            try:
                query = text.split("[CMD: GOOGLE:")[1].split("]")[0].strip()
                result = self.system.search_web(query, "google")
                text = text.replace(f"[CMD: GOOGLE: {query}]", "").strip() + f" ({result})"
            except: pass

        if "[CMD: YTPLAY:" in text:
            try:
                query = text.split("[CMD: YTPLAY:")[1].split("]")[0].strip()
                result = self.system.search_youtube_and_play(query)
                text = text.replace(f"[CMD: YTPLAY: {query}]", "").strip() + f" ({result})"
            except: pass

        if "[CMD: YOUTUBE:" in text:
            try:
                query = text.split("[CMD: YOUTUBE:")[1].split("]")[0].strip()
                result = self.system.search_web(query, "youtube")
                text = text.replace(f"[CMD: YOUTUBE: {query}]", "").strip() + f" ({result})"
            except: pass

        if "[CMD: MEDIA: PLAYPAUSE]" in text:
            try:
                result = self.system.play_pause_media()
                text = text.replace("[CMD: MEDIA: PLAYPAUSE]", "").strip() + f" ({result})"
            except: pass

        if "[CMD: STATS]" in text:
            try:
                result = self.system.get_system_stats()
                text = text.replace("[CMD: STATS]", "").strip() + f" ({result})"
            except: pass

        if "[CMD: LOCATION]" in text:
            try:
                result = self.system.get_precise_location()
                text = text.replace("[CMD: LOCATION]", "").strip() + f" (Sistem Verisi: {result})"
            except: pass

        if "[CMD: WEATHER:" in text:
            try:
                city = text.split("[CMD: WEATHER:")[1].split("]")[0].strip()
                result = self.system.get_weather(city)
                text = text.replace(f"[CMD: WEATHER: {city}]", "").strip() + f" ({result})"
            except: pass

        return text

    def _ask_openrouter(self, custom_history=None):
        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "HTTP-Referer": "https://github.com/veyse/ultron",
            "X-Title": "ULTRON",
        }
        payload = {
            "model": self.api_model,
            "messages": custom_history if custom_history else self.history
        }
        try:
            response = requests.post(self.openrouter_url, headers=headers, json=payload, timeout=20)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return f"API hatasi: {e}"

    def _ask_ollama(self, custom_history=None):
        try:
            tags_resp = requests.get(self.ollama_url.replace("/chat", "/tags"), timeout=2)
            tags_resp.raise_for_status()
            models = tags_resp.json().get("models", [])
            if not models:
                return "Patron, yuklu hicbir Ollama modeli bulamadim."
            active_model = models[0]["name"]
            for m in models:
                if "gemma2" in m["name"]:
                    active_model = m["name"]
                    break
            payload = {
                "model": active_model,
                "messages": custom_history if custom_history else self.history,
                "stream": False
            }
            response = requests.post(self.ollama_url, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()["message"]["content"]
        except Exception as e:
            return f"Offline model hatasi: {str(e)[:80]}"
