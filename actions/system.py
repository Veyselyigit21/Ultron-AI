import pyautogui
import os
import subprocess
import webbrowser
import psutil
import requests
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL
from ctypes import cast, POINTER

class SystemController:
    @staticmethod
    def set_volume(level):
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(
                IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            level = max(0.0, min(1.0, level))
            volume.SetMasterVolumeLevelScalar(level, None)
            return f"Ses seviyesi %{int(level*100)} olarak ayarlandı."
        except Exception as e:
            return f"Ses ayarlanırken hata oluştu: {e}"

    @staticmethod
    def open_application(app_name):
        app_name = app_name.lower()
        paths = {
            "not defteri": "notepad.exe",
            "hesap makinesi": "calc.exe",
            "chrome": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
            "spotify": "spotify",
        }
        target = paths.get(app_name)
        if target:
            try:
                os.startfile(target) if "\\" in target else subprocess.Popen(target)
                return f"{app_name.capitalize()} açıldı."
            except Exception as e:
                return f"{app_name.capitalize()} açılamadı: {e}"
        else:
            return f"{app_name} uygulamasının yolunu bilmiyorum."

    @staticmethod
    def play_pause_media():
        try:
            # Klavyedeki medya durdur/oynat (play/pause) tuşuna sanal olarak basar
            # Arka plandaki Chrome Youtube videolarını, Spotify'ı vb. mükemmel yönetir.
            pyautogui.press('playpause')
            return "Medya oynatıldı/durduruldu."
        except Exception as e:
            return f"Medya kontrol hatası: {e}"

    @staticmethod
    def search_youtube_and_play(query):
        """YouTube'da arama yapar ve ilk videonun watch linkini bularak doğrudan oynatır."""
        import requests, re, webbrowser
        try:
            url = f"https://www.youtube.com/results?search_query={query}"
            html = requests.get(url).text
            video_ids = re.findall(r"watch\?v=(\S{11})", html)
            if video_ids:
                # İlk videoyu direkt aç (YouTube otomatik başlatır)
                webbrowser.open(f"https://www.youtube.com/watch?v={video_ids[0]}")
                return f"YouTube'da '{query}' için ilk video oynatılıyor."
            else:
                webbrowser.open(url)
                return f"YouTube'da '{query}' arandı ama video linki bulunamadı."
        except Exception as e:
            webbrowser.open(f"https://www.youtube.com/results?search_query={query}")
            return f"Arama yapıldı ancak otomatik oynatma başarısız: {e}"

    @staticmethod
    def search_web(query, engine="google"):
        if engine == "youtube":
            webbrowser.open(f"https://www.youtube.com/results?search_query={query}")
            return f"YouTube'da '{query}' aranıyor."
        else:
            webbrowser.open(f"https://www.google.com/search?q={query}")
            return f"Google'da '{query}' aranıyor."

    @staticmethod
    def get_precise_location():
        """Cihazın anlık detaylı konumunu (Enlem, Boylam, Şehir, ISP) IP üzerinden çeker."""
        import requests
        try:
            resp = requests.get("http://ip-api.com/json/?fields=status,country,city,lat,lon,isp,query", timeout=5)
            data = resp.json()
            if data.get("status") == "success":
                return (f"Şehir: {data['city']}, {data['country']} | "
                        f"Enlem (Lat): {data['lat']} | Boylam (Lon): {data['lon']} | "
                        f"ISP: {data['isp']} | IP: {data['query']}")
            return "Konum verisi anlık olarak çekilemedi."
        except Exception as e:
            return f"Konum servisi hatası: {e}"

    @staticmethod
    def get_system_stats():
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory().percent
        return f"CPU Kullanımı: %{cpu}, RAM Kullanımı: %{ram}."

    @staticmethod
    def get_weather(city):
        try:
            url = f"https://api.open-meteo.com/v1/forecast?latitude=41.01&longitude=28.97&current_weather=true" # Default Istanbul
            if city.lower() == "ankara":
                url = f"https://api.open-meteo.com/v1/forecast?latitude=39.92&longitude=32.85&current_weather=true"
            elif city.lower() == "izmir":
                url = f"https://api.open-meteo.com/v1/forecast?latitude=38.41&longitude=27.14&current_weather=true"
            
            resp = requests.get(url).json()
            temp = resp["current_weather"]["temperature"]
            return f"{city.capitalize()} için hava şu an {temp} derece."
        except:
            return "Hava durumu alınamadı."
