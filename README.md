# ULTRON v3

Türkçe sesli masaüstü asistanı. "Ultron" de, konuş; bilgisayarı senin yerine kullansın.

## Kurulum (Windows)
1. `Kur.bat` → venv, paketler, Vosk modelleri (TR+EN) otomatik kurulur.
2. `.env` içine `OPENROUTER_API_KEY=...` yaz (online mod için). Anahtar yoksa offline (Ollama) çalışır.
3. `Baslat_Ultron.bat` (tray'de başlar) veya `Baslat_Pencereli.bat` (pencere + konsol).
4. Windows'la açılsın istersen `Otomatik_Baslat_Ekle.bat`.

Uyandırma: **"Ultron"**, tray ikonu veya **Ctrl+Alt+U**. Uyandıktan sonra 15 sn wake word gerekmez.

## Modlar
`auto` (varsayılan): internet varsa Gemini, yoksa Ollama. "offline moda geç" / "online moda geç" / "otomatik mod".
Offline model yoksa: "ULTRON, qwen2.5:7b modelini indir" → arka planda `ollama pull`.

## Kendini geliştirme
"Ultron, kendine X özelliği ekle" → arka planda kod yazar → AST ile doğrular → paketleri kurar → ayrı süreçte test eder →
**onayını sorar** → yeniden başlatmadan yükler. Kodlar `plugins/` içinde, `plugins/manifest.json` hash tutar (değişirse yüklenmez).
Komutlar: `PLUGIN_LIST`, `PLUGIN_SHOW: ad`, `PLUGIN_REMOVE: ad`. Çekirdek dosyalara dokunmaz.

## Bilgisayar kontrolü
Uygulama aç, web ara/getir, dosya listele/oku/yaz/taşı/sil (geri dönüşüm kutusu), PowerShell/Python çalıştır, süreç sonlandır,
ses, medya, ekran görüntüsü, klavye/fare, pano, kilitle/kapat/uyku, WhatsApp, hava, haber, konum.

**Güvenlik modeli**
- Yıkıcı eylemler (SHELL, dosya yazma/silme, KILL, POWER, TYPE...) her seferinde sesli/ekran onayı ister.
- "Tam yetki 30 dakika" onayı süreli kapatır. Diski biçimlendirme, sürücü kökü/Windows silme, kayıt defteri vb. **her durumda engelli**.
- Web/dosya/pano gibi dış içerik okunduktan sonra gelen komutlar tam yetkide bile onay ister (prompt injection koruması).
- Her eylem `data/logs/actions.log` dosyasına yazılır.

## Testler
`python -m unittest discover -s tests -v`
