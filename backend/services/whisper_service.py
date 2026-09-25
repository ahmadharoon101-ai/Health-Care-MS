"""
Local, offline Whisper speech-to-text service.

The model is loaded exactly once (at FastAPI startup) and reused for every
transcription request. The model is NEVER downloaded automatically — it
must already exist as a local file under WHISPER_MODEL_PATH
(e.g. backend/models/whisper/base.pt). This keeps the system usable in
network-restricted / offline hospital environments.
"""

import logging
import threading
from pathlib import Path
from typing import Optional

from backend import config

logger = logging.getLogger("whisper_service")


class WhisperNotAvailableError(Exception):
    """Raised when the model file/library isn't available for transcription."""


class WhisperService:
    def __init__(self):
        self._model = None
        self._load_error: Optional[str] = None
        # openai-whisper's model.transcribe() is not guaranteed safe to call
        # concurrently from multiple threads on the same model instance.
        # Since the whole app shares one loaded model, serialize access so
        # two doctors recording at the same time queue up safely instead of
        # racing inside PyTorch.
        self._lock = threading.Lock()

    def load(self) -> None:
        """Load the local Whisper model once. Called at app startup."""
        model_file = config.WHISPER_MODEL_PATH / f"{config.WHISPER_MODEL_NAME}.pt"

        if not model_file.exists():
            self._load_error = (
                f"Whisper model file not found at '{model_file}'. "
                f"Download the '{config.WHISPER_MODEL_NAME}' model weights once "
                f"(on a machine with internet access) and place the .pt file "
                f"in that folder. The backend will not download it automatically."
            )
            logger.warning(self._load_error)
            return

        try:
            import whisper  # openai-whisper package
        except ImportError:
            self._load_error = (
                "The 'openai-whisper' package is not installed. "
                "Run: pip install -r requirements.txt"
            )
            logger.error(self._load_error)
            return

        try:
            self._model = whisper.load_model(
                config.WHISPER_MODEL_NAME,
                device=config.WHISPER_DEVICE,
                download_root=str(config.WHISPER_MODEL_PATH),
            )
            logger.info(
                "Whisper model '%s' loaded on device '%s'",
                config.WHISPER_MODEL_NAME,
                config.WHISPER_DEVICE,
            )
        except Exception as exc:  # pragma: no cover - defensive
            self._load_error = f"Failed to load Whisper model: {exc}"
            logger.exception(self._load_error)
            self._model = None

    @property
    def is_ready(self) -> bool:
        return self._model is not None

    @property
    def load_error(self) -> Optional[str]:
        return self._load_error

    def transcribe(self, audio_path: str) -> str:
        """
        Transcribe an audio file on disk and return the recognized text.

        This is a blocking, CPU-bound call (can take a few seconds). It must
        only ever be invoked off the asyncio event loop (see
        backend/websocket/voice.py, which runs it via asyncio.to_thread) so
        that one doctor's transcription never freezes the whole server for
        everyone else (other voice sessions, medicine search, health checks).
        """
        if self._model is None:
            raise WhisperNotAvailableError(
                self._load_error or "Whisper model is not loaded."
            )

        with self._lock:
            result = self._model.transcribe(
                audio_path,
                language=config.WHISPER_LANGUAGE,
                fp16=False,  # CPU-safe
            )
        text = (result.get("text") or "").strip()
        return text


# Single shared instance, loaded once at application startup.
whisper_service = WhisperService()
