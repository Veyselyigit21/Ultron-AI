"""Terminal modu (arayüzsüz): yazarak konuş. Sesli/arayüzlü kullanım için main_gui.py."""
import sys

from core.llm_manager import LLMManager


def main():
    done = {"quit": False}

    def on_event(name, payload=None):
        if name == "notify":
            print(f"\nULTRON: {payload}")
        elif name == "quit":
            done["quit"] = True

    llm = LLMManager(on_event=on_event)
    print("ULTRON terminal modu. Çıkmak için 'kapat'.")
    while not done["quit"]:
        try:
            t = input("sen> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if t:
            print("ULTRON:", llm.ask(t))
    return 0


if __name__ == "__main__":
    sys.exit(main())
