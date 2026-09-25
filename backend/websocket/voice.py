"""
WebSocket endpoint: /ws/voice

Protocol (simple and framework-agnostic on the frontend side):

  Client -> Server
    - Text message {"type": "start"}                 : begin a new recording
    - Binary frames                                    : raw audio chunks (webm/opus)
    - Text message {"type": "stop"}                   : recording finished, please transcribe
    - Text message {"type": "cancel"}                 : discard current recording

  Server -> Client (all JSON text frames)
    - {"type": "status",  "message": "listening"}
    - {"type": "status",  "message": "processing"}
    - {"type": "result",  "text": "Panadol"}
    - {"type": "error",   "message": "..."}

Audio chunks are buffered in memory for the duration of one recording and
written to a single temp file once the doctor stops recording, then handed
to the (already-loaded) Whisper model for transcription.
"""

import asyncio
import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend import config
from backend.services.whisper_service import whisper_service, WhisperNotAvailableError
from backend.utils.text_normalizer import is_empty

logger = logging.getLogger("websocket.voice")
router = APIRouter()


async def _send_json(ws: WebSocket, payload: dict) -> None:
    try:
        await ws.send_json(payload)
    except Exception:  # connection may already be gone
        pass


@router.websocket("/ws/voice")
async def voice_endpoint(websocket: WebSocket):
    await websocket.accept()
    audio_chunks: list[bytes] = []
    recording = False

    await _send_json(websocket, {"type": "status", "message": "connected"})

    try:
        while True:
            message = await websocket.receive()

            if message.get("type") == "websocket.disconnect":
                break

            # Binary audio chunk
            if "bytes" in message and message["bytes"] is not None:
                if not recording:
                    # Ignore stray audio sent before a "start" message
                    continue
                audio_chunks.append(message["bytes"])
                continue

            # Text control message
            if "text" in message and message["text"] is not None:
                import json

                try:
                    control = json.loads(message["text"])
                except ValueError:
                    await _send_json(
                        websocket, {"type": "error", "message": "Invalid control message."}
                    )
                    continue

                msg_type = control.get("type")

                if msg_type == "start":
                    audio_chunks = []
                    recording = True
                    await _send_json(websocket, {"type": "status", "message": "listening"})

                elif msg_type == "cancel":
                    audio_chunks = []
                    recording = False
                    await _send_json(websocket, {"type": "status", "message": "cancelled"})

                elif msg_type == "stop":
                    recording = False
                    await _send_json(
                        websocket, {"type": "status", "message": "processing voice..."}
                    )

                    if not audio_chunks:
                        await _send_json(
                            websocket,
                            {
                                "type": "error",
                                "message": "No audio was captured. Please try again.",
                            },
                        )
                        continue

                    text = await _transcribe_chunks(audio_chunks)
                    audio_chunks = []

                    if text is None:
                        await _send_json(
                            websocket,
                            {
                                "type": "error",
                                "message": "Unable to process the voice input. Please try again.",
                            },
                        )
                        continue

                    if is_empty(text):
                        await _send_json(
                            websocket,
                            {
                                "type": "error",
                                "message": "No speech was detected. Please try again.",
                            },
                        )
                        continue

                    await _send_json(websocket, {"type": "result", "text": text.strip()})

                else:
                    await _send_json(
                        websocket, {"type": "error", "message": f"Unknown message type: {msg_type}"}
                    )

    except WebSocketDisconnect:
        logger.info("Voice WebSocket client disconnected")
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Unexpected error in voice websocket: %s", exc)
        await _send_json(
            websocket, {"type": "error", "message": "A server error occurred. Please try again."}
        )


async def _transcribe_chunks(chunks: list[bytes]) -> str | None:
    """Write buffered audio to a temp file and run it through Whisper."""
    temp_path: Path = config.TEMP_AUDIO_DIR / f"{uuid.uuid4().hex}.webm"
    try:
        with open(temp_path, "wb") as f:
            for chunk in chunks:
                f.write(chunk)

        try:
            # Run the blocking Whisper call in a worker thread so it never
            # freezes the event loop — otherwise one doctor's transcription
            # would stall every other request (other voice sessions,
            # medicine search, health checks) for the duration of decoding.
            return await asyncio.to_thread(whisper_service.transcribe, str(temp_path))
        except WhisperNotAvailableError as exc:
            logger.error("Whisper unavailable: %s", exc)
            return None
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Whisper transcription failed: %s", exc)
            return None
    finally:
        try:
            temp_path.unlink(missing_ok=True)
        except Exception:
            pass
