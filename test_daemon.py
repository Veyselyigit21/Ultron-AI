import threading
import time

def listen_loop():
    print("Listening loop started.")
    try:
        from vosk import Model, KaldiRecognizer
        print("Vosk imported.")
    except Exception as e:
        print("Error:", e)
    time.sleep(1)
    print("Listen loop end.")

if __name__ == "__main__":
    t = threading.Thread(target=listen_loop)
    t.start()
    t.join()
