path = r"D:\ultron\senses\voice.py"
with open(path, "r", encoding="utf-8") as f:
    code = f.read()

# Fix TTS command
old_cmd = """            result = subprocess.run(
                [self.edge_tts, '--voice', 'tr-TR-AhmetNeural', '--text', clean_text, '--write-media', output_file],
                capture_output=True, timeout=15, creationflags=subprocess.CREATE_NO_WINDOW
            )"""
new_cmd = """            import sys
            result = subprocess.run(
                [sys.executable, '-m', 'edge_tts', '--voice', 'tr-TR-AhmetNeural', '--text', clean_text, '--write-media', output_file],
                capture_output=True, timeout=15, creationflags=subprocess.CREATE_NO_WINDOW
            )"""
code = code.replace(old_cmd, new_cmd)

with open(path, "w", encoding="utf-8") as f:
    f.write(code)
print("TTS patched!")
