import asyncio
import configparser
import argparse
import logging
import os

from pynput import keyboard
from utils import RealtimeClient, AudioHandler, TurnDetectionMode, InputHandler, logger

# Argument parser
parser = argparse.ArgumentParser(description="Realtime API CLI with Server VAD")
parser.add_argument("--debug", action="store_true")
args = parser.parse_args()

if args.debug:
    logger.setLevel(logging.DEBUG)

# Read configuration
current_dir = os.path.dirname(os.path.realpath(__file__))
config_path = os.path.join(current_dir, "config.ini")
config = configparser.ConfigParser()
config.read(config_path)
OPENAI_KEY = config["DEFAULT"]["OPENAI_KEY"]

async def main():
    audio_handler = AudioHandler()
    input_handler = InputHandler()
    input_handler.loop = asyncio.get_running_loop()
    
    client = RealtimeClient(
        api_key = OPENAI_KEY,
        on_text_delta=lambda text: print(f"Assistant: {text}", end="", flush=True),
        on_audio_delta=lambda audio: audio_handler.play_audio(audio),
        on_interrupt=lambda: audio_handler.stop_playback_immediately(),
        turn_detection_mode=TurnDetectionMode.SERVER_VAD,
    )

    # Start keyboard listener in a separate thread
    listener = keyboard.Listener(on_press=input_handler.on_press)
    listener.start()
    
    try:
        await client.connect()
        message_handler = asyncio.create_task(client.handle_messages())
        
        logger.info("Connected to OpenAI Realtime API!")
        logger.info("Audio streaming will start automatically.")
        logger.info("Press 'q' to quit\n")
        
        # Start continuous audio streaming
        streaming_task = asyncio.create_task(audio_handler.start_streaming(client))
        
        # Simple input loop for quit command
        while True:
            command, _ = await input_handler.command_queue.get()
            
            if command == 'q':
                break
            
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        audio_handler.stop_streaming()
        audio_handler.cleanup()
        await client.close()

if __name__ == "__main__":
    logger.info("Starting Realtime API CLI with Server VAD...")
    asyncio.run(main())