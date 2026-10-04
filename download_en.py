import urllib.request
import zipfile
import os

url = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
zip_path = r"D:\ultron\vosk-model-en.zip"
extract_path = r"D:\ultron"

print("Indiriliyor...")
urllib.request.urlretrieve(url, zip_path)
print("Indirme tamamlandi. Cikariliyor...")

with zipfile.ZipFile(zip_path, 'r') as zip_ref:
    zip_ref.extractall(extract_path)

os.rename(r"D:\ultron\vosk-model-small-en-us-0.15", r"D:\ultron\vosk-model-en")
os.remove(zip_path)
print("Ingilizce model hazir.")
