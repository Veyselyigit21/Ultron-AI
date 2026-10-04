import webbrowser
import time
import pyautogui

class WhatsAppController:
    def __init__(self):
        pass

    def send_message(self, contact_name, message):
        try:
            # WhatsApp Web'i varsayılan tarayıcıda aç
            webbrowser.open("https://web.whatsapp.com/")
            
            # Sayfanın yüklenmesi için bekle (İlk seferde QR kod gerekebilir)
            time.sleep(10)
            
            # WhatsApp Web'de Arama kutusuna odaklanmak için kısayol: Ctrl + Alt + /
            pyautogui.hotkey('ctrl', 'alt', '/')
            time.sleep(1)
            
            # Kişi adını yaz
            pyautogui.write(contact_name)
            time.sleep(2) # Arama sonuçlarının gelmesini bekle
            
            # Çıkan ilk kişiyi seç (Enter)
            pyautogui.press('enter')
            time.sleep(2)
            
            # Mesajı yaz
            pyautogui.write(message)
            time.sleep(1)
            
            # Gönder (Enter)
            pyautogui.press('enter')
            
            return f"WhatsApp üzerinden {contact_name} kişisine mesaj denendi."
            
        except Exception as e:
            return f"WhatsApp işlemi sırasında hata oluştu: {e}"
