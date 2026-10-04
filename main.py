import os
from colorama import init, Fore, Style
from core.llm_manager import LLMManager
from senses.hearing import Ear
from senses.voice import Mouth

# Colorama'yı başlat
init(autoreset=True)

def print_ultron(text):
    print(f"{Fore.CYAN}{Style.BRIGHT}E.D.I.T.H:{Style.NORMAL} {text}")

def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print(f"{Fore.YELLOW}Sistemler yükleniyor... Lütfen bekleyin.{Style.NORMAL}")
    
    # E.D.I.T.H.'in beyni, kulağı ve ağzı
    llm = LLMManager(use_local=False, api_model="google/gemini-2.5-flash")
    ear = Ear()
    mouth = Mouth()
    
    # Açılış
    os.system('cls' if os.name == 'nt' else 'clear')
    greeting = "Sistemler devrede. Tüm protokoller aktif. Nasıl yardımcı olabilirim patron?"
    print_ultron(greeting)
    mouth.speak(greeting)
    
    while True:
        try:
            # Klavyeden girmek yerine mikrofondan dinliyoruz
            user_input = ear.listen()
            
            if not user_input:
                continue
                
            if "kapat" in user_input.lower() or "çıkış" in user_input.lower() or "sistemi kapat" in user_input.lower():
                farewell = "Sistem kapatılıyor. Görüşmek üzere patron."
                print_ultron(farewell)
                mouth.speak(farewell)
                break
                
            response = llm.ask(user_input)
            print_ultron(response)
            mouth.speak(response)
            
        except KeyboardInterrupt:
            print()
            print_ultron("Acil çıkış protokolü. Sistem kapatılıyor...")
            break

if __name__ == "__main__":
    main()
