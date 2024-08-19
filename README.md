# Učitel autoškoly - Asistent

## Popis projektu

Tento prototyp používá OpenAI API pro vytvoření virtuálního učitel autoškoly. Využíváný model je klasický openAI model. Tento model byl naučený na datech z celého internetu, které také obsahovali české dopravní pravidla, a proto je model schopný korektně odpovídat na dotazy.

Aplikace umožňuje uživateli nahrávat dotazy prostřednictvím textu nebo zvuku (předpokládá se český jazyk, pohlaví či věk nemá vliv). Zvuk je pomocí openAI Whisper modelu přepsán na text. Aplikace poté umožňuje poskytnutí textové odpovědi od virtuálního učitele, která je zobrazena v grafickém uživatelském rozhraní (GUI). GUI je primitivní a slouží pouze k demonstraci funkcionality aplikace. 

## Postup instalace

0. Předpoklady:
- Python 3.10 nebo novější

1. Naklonujte repozitář:

Buďto přes příkazovou řádku:
```bash
git clone
cd autoskola-assistant
```
Nebo stáhněte zip soubor repozitáře a rozbalte ho.

2. Nainstalujte požadované závislosti:

```bash
pip install openai pyaudio tenacity
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

3. Updatujte konfigurační soubor config.ini:
V souboru config.ini upravte hodnoty OPENAI_KEY z YOUR_OPENAI_KEY na váš openAI API klíč. Případně je i možnost změnit GPT_MODEL na jiný model, který je podporován openAI, ale není to nutné.

4. Spusťte aplikaci:

Pomocí příkazové řádky:
```bash
python main.py
```
Nebo rozkliknutím main.py souboru.