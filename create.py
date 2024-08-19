import configparser
import logging
import openai
import asyncio
import pyaudio
import wave
import tkinter as tk
from tkinter import scrolledtext
import tempfile  # Import the tempfile module
from utils import (
    chat_completion_request,
    RequestParams,
)

# Logging setup
logging.basicConfig(level=logging.INFO)

# Read configuration
config = configparser.ConfigParser()
config.read("config.ini")
OPENAI_KEY = config["DEFAULT"]["OPENAI_KEY"]
GPT_MODEL = config["DEFAULT"]["GPT_MODEL"]

def record_audio(filename, duration=5, sample_rate=44100, chunk_size=1024):
    audio_format = pyaudio.paInt16
    channels = 1
    chunk = chunk_size
    record_seconds = duration

    audio = pyaudio.PyAudio()

    stream = audio.open(format=audio_format, channels=channels,
                        rate=sample_rate, input=True,
                        frames_per_buffer=chunk)

    print("Recording...")

    frames = []

    for _ in range(0, int(sample_rate / chunk * record_seconds)):
        data = stream.read(chunk)
        frames.append(data)

    print("Finished recording.")

    stream.stop_stream()
    stream.close()
    audio.terminate()

    # Write audio frames to the temporary file
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(audio.get_sample_size(audio_format))
        wf.setframerate(sample_rate)
        wf.writeframes(b''.join(frames))

async def transcribe_audio():
    client = openai.AsyncClient(api_key=OPENAI_KEY)

    # Use tempfile to create a temporary audio file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
        temp_filename = temp_audio.name
        # Record audio into the temporary file
        record_audio(temp_filename, duration=10)
        
        # After recording, open the temporary file for reading
        with open(temp_filename, "rb") as file:
            transcript = await client.audio.transcriptions.create(
                model="whisper-1", file=file, language="cs"
            )

    return transcript.text

async def generate_response(instructions, transcript):
    client = openai.AsyncClient(api_key=OPENAI_KEY)

    messages = [
        {"role": "system", "content": instructions},
        {"role": "user", "content": transcript},
    ]

    params = RequestParams(
        client=client,
        messages=messages,
        max_tokens=3000,
        temperature=0.5,
        top_p=0.5,
    )

    response = await chat_completion_request(params)
    return response.choices[0].message.content

def start_audio_recording():
    input_text.delete("1.0", tk.END)
    loop = asyncio.get_event_loop()
    transcript = loop.run_until_complete(transcribe_audio())
    input_text.insert(tk.END, transcript)

def generate_message():
    instructions = """Jsi zkušený učitel autoškoly, který dokonale ovládá česká dopravní pravidla a zákony. Odpovídáš pouze na otázky, které ti žák klade, a soustředíš se na to, aby byly tvoje odpovědi vždy přesné a stručné. Vždy používáš aktuální česká dopravní pravidla. Pokud je třeba, vysvětluješ situace na konkrétních příkladech z reálného provozu. Nezabýváš se informacemi, které nejsou relevantní k otázce žáka."""
    prompt = input_text.get("1.0", tk.END)
    loop = asyncio.get_event_loop()
    response = loop.run_until_complete(generate_response(instructions, prompt))
    output_text.delete("1.0", tk.END)
    output_text.insert(tk.END, response)

# GUI setup
root = tk.Tk()
root.title("OpenAI GUI")

# Input Text Field
input_label = tk.Label(root, text="Vstup:")
input_label.pack()

input_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=100, height=10)
input_text.pack()

# Record Audio Button
record_button = tk.Button(root, text="Nahrát zvuk", command=start_audio_recording)
record_button.pack()

# Generate Message Button
generate_button = tk.Button(root, text="Generuj zprávu", command=generate_message)
generate_button.pack()

# Output Text Field
output_label = tk.Label(root, text="Výstup:")
output_label.pack()

output_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=100, height=40)
output_text.pack()

# Start the Tkinter event loop
root.mainloop()
