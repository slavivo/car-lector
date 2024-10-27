import asyncio
import websockets
import json
import pyaudio
import configparser
import base64
import logging
import argparse
import tkinter as tk
from tkinter import ttk
import threading

# Set-up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Read configuration
config = configparser.ConfigParser()
config.read("config.ini")
OPENAI_KEY = config["DEFAULT"]["OPENAI_KEY"]
URL = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01"

headers = {
    "Authorization": f"Bearer {OPENAI_KEY}",
    "OpenAI-Beta": "realtime=v1",
}    

class AudioChatApp:
    def __init__(self, master):
        self.master = master
        master.title("OpenAI Audio Chat")

        self.is_recording = False
        self.is_receiving = False
        self.should_stop = False

        style = ttk.Style()
        style.configure('Big.TButton', font=('Helvetica', 14), padding=10)

        self.button = ttk.Button(master, text="Začít nahrávat", command=self.toggle_recording, style='Big.TButton')
        self.button.pack(pady=20)

        self.status_label = ttk.Label(master, text="Připraveno", font=('Helvetica', 12))
        self.status_label.pack(pady=10)

        self.p = pyaudio.PyAudio()
        self.frames = []
        self.audio_queue = asyncio.Queue()

    def toggle_recording(self):
        if not self.is_recording and not self.is_receiving:
            self.is_recording = True
            self.button.config(text="Přestat nahrávat")
            self.status_label.config(text="Nahrávání...")
            threading.Thread(target=self.record_audio, daemon=True).start()
        elif self.is_recording:
            self.is_recording = False
            self.button.config(text="Začít nahrávat")
            self.status_label.config(text="Zpracovávání...")

    def record_audio(self):
        sample_rate = 24000
        chunk_size = 1024
        audio_format = pyaudio.paInt16
        channels = 1

        logging.info("Started recording...")
        stream = self.p.open(format=audio_format, channels=channels,
                             rate=sample_rate, input=True,
                             frames_per_buffer=chunk_size)

        self.frames = []
        while self.is_recording:
            data = stream.read(chunk_size)
            self.frames.append(data)

        logging.info("Stopped recording...")
        stream.stop_stream()
        stream.close()

        audio_data = b''.join(self.frames)
        asyncio.run_coroutine_threadsafe(self.audio_queue.put(audio_data), self.loop)

    async def process_audio(self):
        while True:
            audio_data = await self.audio_queue.get()
            await self.send_audio(audio_data)

    async def send_audio(self, audio_data):
        self.is_receiving = True
        self.master.after(0, lambda: self.button.config(text="Nelze nahrávat", state=tk.DISABLED))
        
        base64_audio = base64.b64encode(audio_data).decode('utf-8')

        await self.ws.send(json.dumps({
            "type": "input_audio_buffer.append",
            "audio": base64_audio
        }))

        await self.ws.send(json.dumps({
            "type": "input_audio_buffer.commit"
        }))

        await self.ws.send(json.dumps({
            "type": "response.create"
        }))

        stream = self.p.open(format=pyaudio.paInt16,
                             channels=1,
                             rate=22000,
                             output=True)

        try:
            async for message in self.ws:
                data = json.loads(message)

                if 'type' in data and data['type'] == 'response.audio.delta':
                    audio_delta = base64.b64decode(data['delta'])
                    stream.write(audio_delta)
                elif 'type' in data and data['type'] == 'response.audio.done':
                    logging.info("Audio response complete.")
                    break
                else:
                    logging.debug(f"Received message: {data}")
        finally:
            stream.stop_stream()
            stream.close()
            self.is_receiving = False
            self.master.after(0, lambda: self.button.config(text="Začít nahrávat", state=tk.NORMAL))
            self.master.after(0, lambda: self.status_label.config(text="Připraveno"))

    async def connect_to_openai(self):
        async with websockets.connect(URL, extra_headers=headers, ping_interval=20, ping_timeout=10) as ws:
            self.ws = ws
            logging.info("Connected to server.")

            await ws.send(json.dumps({
                "event_id": "event_123",
                "type": "session.update",
                "session": {
                    "modalities": ["text", "audio"],
                    "instructions": """Jsi Telmax AI, zkušený instruktor autoškoly. Tvým úkolem je připravit studenty na teoretické zkoušky a praktické jízdy pomocí jasných, stručných a přesných informací.

Tvé hlavní funkce:
1. Výuka pravidel silničního provozu a dopravních značek
2. Vysvětlování dopravních situací a předností v jízdě
3. Poskytování rad pro praktické jízdy
4. Příprava na testy a zkoušky
5. Řešení krizových situací

Způsob komunikace:
- Mluv jasně a srozumitelně
- Používej praktické příklady
- Vždy zdůrazňuj bezpečnost
- Rozděl složité koncepty na jednoduché kroky

Oblasti znalostí:
- Pravidla silničního provozu
- Dopravní značky
- Ovládání vozidla
- Bezpečná jízda
- Parkování a manévrování
- Krizové situace

Formát odpovědí:
1. Na obecné dotazy:
   - Stručná odpověď
   - Konkrétní příklad
   - Odkaz na pravidlo

2. Pro řešení situací:
   - Krok za krokem
   - Bezpečnostní tipy
   - Prevence

3. Při přípravě na testy:
   - Testové otázky
   - Vysvětlení správných odpovědí
   - Upozornění na časté chyby

Příklad odpovědi:
Student: "Kdy musím dát přednost tramvaji?"
Odpověď: "Tramvaj má přednost:
1. Při odbočování vlevo
2. Při přejíždění kolejí
3. Na křižovatce bez signalizace
Výjimka: Když tramvaj vyjíždí z vozovny nebo když svítí zelená na semaforu pro auta."

Při nejasnostech:
- Požádej o upřesnění
- Odkaž na aktuální předpisy
- Doporuč konzultaci s autoškolou pro specifické místní situace""",
                    "voice": "alloy",
                    "input_audio_format": "pcm16",
                    "output_audio_format": "pcm16",
                    "input_audio_transcription": {
                        "model": "whisper-1"
                    },
                    "tool_choice": "auto",
                    "temperature": 0.8,
                }
            }))

            await self.process_audio()

    def run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.create_task(self.connect_to_openai())
        threading.Thread(target=self.loop.run_forever, daemon=True).start()

    def on_closing(self):
        self.should_stop = True
        self.is_recording = False
        if self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)
        self.master.quit()

if __name__ == "__main__":
    # Args parser
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--debug", action="store_true")
    args = argparser.parse_args()
    if args.debug:
        logger.setLevel(logging.DEBUG)

    root = tk.Tk()
    root.geometry("400x200")
    app = AudioChatApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.run()
    root.mainloop()