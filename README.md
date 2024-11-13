# Real-time konverzace

## Popis projektu

Tento prototyp používá OpenAI Realtime API pro vytvoření virtuálního učitele/asistenta.
Aplikace umožňuje uživateli konverzaci s virtuálním asistentem. Stačí pouze kliknout na tlačítko "Začít nahrávat" pro zahájení nahrávání hlasu uživatele a poté "Přestat nahrávat" pro zastavení nahrání. Následně openAI zpracuje odpověď, která se poté přehraje. Toto lze opakovat jako v konverzaci.

## Postup instalace

0. Předpoklady:
- Python 3.10 nebo novější

1. Naklonujte repozitář:

Buďto stáhněte zip soubor repozitáře a rozbalte ho.
Nebo přes příkazovou řádku:
```bash
git clone https://github.com/slavivo/car-lector.git
cd car-lector
```

2. Nainstalujte požadované závislosti:

```bash
pip install PyAudio==0.2.14 pydub==0.25.1 pynput==1.7.7 websockets==12.0
```

Pokud nastane chyba při instalaci knihovny pyaudio, zkuste nainstalovat balíček portaudio pomocí následujícího příkazu:

Linux:
```bash
sudo apt-get install portaudio19-dev
```
Apple:
```bash
brew install portaudio
```

3. Ve složce src vytvořte soubor **config.ini**, který bude mít strukturu:

```ini
[DEFAULT]
OPENAI_KEY = <YOUR_KEY>
```
Místo <YOUR_KEY> doplňte váš OpenAI klíč.

4. Spusťte aplikaci:

Máte dvě možnosti aplikací:
- main.py - Spustí aplikaci s grafickým rozhraním, kde se musí klikat na tlačítko pro zahájení a zastavení nahrávání.
- realtime.py - Spustí aplikaci bez grafického rozhraní, kde se nahrávání spouští a zastavuje automaticky.

Pomocí příkazové řádky (případně main.py nahraďte za realtime.py):
```bash
python main.py
```
Nebo rozkliknutím main.py souboru ve složce src.