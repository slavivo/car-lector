# Učitel autoškoly - Asistent

## Popis projektu

Tento prototyp používá OpenAI Realtime API pro vytvoření virtuálního učitel autoškoly. Toto API využívá několik openAI modelů pro přepsání hlasu uživatele, generování nové odpovědi a vytvoření hlasu pro tuto odpověď. 
Model použitý pro generování odpovědi je klasický openAI model gpt-4o. Tento model byl naučený na datech z celého internetu, které také obsahovali české dopravní pravidla, a proto je model schopný korektně odpovídat na dotazy.

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
pip install websockets pyaudio
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
V souboru config.ini upravte hodnoty OPENAI_KEY z YOUR_OPENAI_KEY na váš openAI API klíč. 

4. Spusťte aplikaci:

Pomocí příkazové řádky:
```bash
python main.py
```
Nebo rozkliknutím main.py souboru.