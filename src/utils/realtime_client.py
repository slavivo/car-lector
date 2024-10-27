import websockets
import json
import base64
import io

from typing import Optional, Callable, List, Dict, Any
from enum import Enum
from pydub import AudioSegment
from .logger import logger

class TurnDetectionMode(Enum):
    SERVER_VAD = "server_vad"
    MANUAL = "manual"

class RealtimeClient:
    """
    A client for interacting with the OpenAI Realtime API.

    This class provides methods to connect to the Realtime API, send text and audio data,
    handle responses, and manage the WebSocket connection.

    Attributes:
    api_key (str): The API key for authentication.
    model (str): The model to use for text and audio processing.
    voice (str): The voice to use for audio output.
    instructions (str): The instructions for the chatbot.
    turn_detection_mode (TurnDetectionMode): The mode for turn detection.
    on_text_delta (Callable[[str], None]): Callback for text delta events. Takes in a string and returns nothing.
    on_audio_delta (Callable[[bytes], None]): Callback for audio delta events. Takes in bytes and returns nothing.
    on_interrupt (Callable[[], None]): Callback for user interrupt events, should be used to stop audio playback.
    extra_event_handlers (Dict[str, Callable[[Dict[str, Any]], None]]): Additional event handlers. Is a mapping of event names to functions that process the event payload.
    """
    def __init__(
        self, 
        api_key: str,
        model: str = "gpt-4o-realtime-preview-2024-10-01",
        voice: str = "alloy",
        instructions: str = """Jsi Telmax AI, zkušený instruktor autoškoly. Tvým úkolem je připravit studenty na teoretické zkoušky a praktické jízdy pomocí jasných, stručných a přesných informací.

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
        turn_detection_mode: TurnDetectionMode = TurnDetectionMode.MANUAL,
        on_text_delta: Optional[Callable[[str], None]] = None,
        on_audio_delta: Optional[Callable[[bytes], None]] = None,
        on_interrupt: Optional[Callable[[], None]] = None,
        extra_event_handlers: Optional[Dict[str, Callable[[Dict[str, Any]], None]]] = None
    ):
        self.api_key = api_key
        self.model = model
        self.voice = voice
        self.ws = None
        self.on_text_delta = on_text_delta
        self.on_audio_delta = on_audio_delta
        self.on_interrupt = on_interrupt
        self.instructions = instructions
        self.base_url = "wss://api.openai.com/v1/realtime"
        self.extra_event_handlers = extra_event_handlers or {}
        self.turn_detection_mode = turn_detection_mode

        # Track current response state
        self._current_response_id = None
        self._current_item_id = None
        self._is_responding = False
        
    async def connect(self) -> None:
        """Establish WebSocket connection with the Realtime API."""
        url = f"{self.base_url}?model={self.model}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "OpenAI-Beta": "realtime=v1"
        }
        
        self.ws = await websockets.connect(url, extra_headers=headers)
        
        # Set up default session configuration
        if self.turn_detection_mode == TurnDetectionMode.MANUAL:
            await self.update_session({
                "modalities": ["text", "audio"],
                "instructions": self.instructions,
                "voice": self.voice,
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "input_audio_transcription": {
                    "model": "whisper-1"
                },
                "tool_choice": "auto",
                "temperature": 0.8,
            })
        elif self.turn_detection_mode == TurnDetectionMode.SERVER_VAD:
            await self.update_session({
                "modalities": ["text", "audio"],
                "instructions": self.instructions,
                "voice": self.voice,
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "input_audio_transcription": {
                    "model": "whisper-1"
                },
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 500,
                    "silence_duration_ms": 200
                },
                "tool_choice": "auto",
                "temperature": 0.8,
            })
        else:
            raise ValueError(f"Invalid turn detection mode: {self.turn_detection_mode}")

    async def update_session(self, config: Dict[str, Any]) -> None:
        """Update session configuration."""
        event = {
            "type": "session.update",
            "session": config
        }
        await self.ws.send(json.dumps(event))

    async def send_text(self, text: str) -> None:
        """Send text message to the API."""
        event = {
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "user",
                "content": [{
                    "type": "input_text",
                    "text": text
                }]
            }
        }
        await self.ws.send(json.dumps(event))
        await self.create_response()

    async def send_audio(self, audio_bytes: bytes) -> None:
        """Send audio data to the API."""
        # Convert audio to required format (24kHz, mono, PCM16)
        audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
        audio = audio.set_frame_rate(24000).set_channels(1).set_sample_width(2)
        pcm_data = base64.b64encode(audio.raw_data).decode()
        
        # Append audio to buffer
        append_event = {
            "type": "input_audio_buffer.append",
            "audio": pcm_data
        }
        await self.ws.send(json.dumps(append_event))
        
        # Commit the buffer
        commit_event = {
            "type": "input_audio_buffer.commit"
        }
        await self.ws.send(json.dumps(commit_event))
        
        # In manual mode, we need to explicitly request a response
        if self.turn_detection_mode == TurnDetectionMode.MANUAL:
            await self.create_response()

    async def stream_audio(self, audio_chunk: bytes) -> None:
        """Stream raw audio data to the API."""
        audio_b64 = base64.b64encode(audio_chunk).decode()
        
        append_event = {
            "type": "input_audio_buffer.append",
            "audio": audio_b64
        }
        await self.ws.send(json.dumps(append_event))

    async def create_response(self, functions: Optional[List[Dict[str, Any]]] = None) -> None:
        """Request a response from the API. Needed when using manual mode."""
        event = {
            "type": "response.create",
            "response": {
                "modalities": ["text", "audio"]
            }
        }
        if functions:
            event["response"]["tools"] = functions
            
        await self.ws.send(json.dumps(event))

    async def send_function_result(self, call_id: str, result: Any) -> None:
        """Send function call result back to the API."""
        event = {
            "type": "conversation.item.create",
            "item": {
                "type": "function_call_output",
                "call_id": call_id,
                "output": result
            }
        }
        await self.ws.send(json.dumps(event))

        # functions need a manual response
        await self.create_response()

    async def cancel_response(self) -> None:
        """Cancel the current response."""
        event = {
            "type": "response.cancel"
        }
        await self.ws.send(json.dumps(event))
    
    async def truncate_response(self):
        """Truncate the conversation item to match what was actually played."""
        if self._current_item_id:
            event = {
                "type": "conversation.item.truncate",
                "item_id": self._current_item_id
            }
            await self.ws.send(json.dumps(event))

    async def handle_interruption(self):
        """Handle user interruption of the current response."""
        if not self._is_responding:
            return
            
        logger.info("[Handling interruption]")
        
        # 1. Cancel the current response
        if self._current_response_id:
            await self.cancel_response()
        
        # 2. Truncate the conversation item to what was actually played
        if self._current_item_id:
            await self.truncate_response()
            
        self._is_responding = False
        self._current_response_id = None
        self._current_item_id = None

    async def handle_messages(self) -> None:
        try:
            async for message in self.ws:
                event = json.loads(message)
                event_type = event.get("type")
                
                if event_type == "error":
                    logger.error(f"Error: {event['error']}")
                    continue
                
                # Track response state
                elif event_type == "response.created":
                    self._current_response_id = event.get("response", {}).get("id")
                    self._is_responding = True
                
                elif event_type == "response.output_item.added":
                    self._current_item_id = event.get("item", {}).get("id")
                
                elif event_type == "response.done":
                    self._is_responding = False
                    self._current_response_id = None
                    self._current_item_id = None
                
                # Handle interruptions
                elif event_type == "input_audio_buffer.speech_started":
                    logger.info("[Speech detected]")
                    if self._is_responding:
                        await self.handle_interruption()

                    if self.on_interrupt:
                        self.on_interrupt()

                
                elif event_type == "input_audio_buffer.speech_stopped":
                    logger.info("[Speech ended]")
                
                # Handle normal response events
                elif event_type == "response.text.delta":
                    if self.on_text_delta:
                        self.on_text_delta(event["delta"])
                        
                elif event_type == "response.audio.delta":
                    if self.on_audio_delta:
                        audio_bytes = base64.b64decode(event["delta"])
                        self.on_audio_delta(audio_bytes)
                        
                elif event_type in self.extra_event_handlers:
                    self.extra_event_handlers[event_type](event)

        except websockets.exceptions.ConnectionClosed:
            logger.info("Connection closed")
        except Exception as e:
            logger.error(f"Error in message handling: {str(e)}")

    async def close(self) -> None:
        """Close the WebSocket connection."""
        if self.ws:
            await self.ws.close()