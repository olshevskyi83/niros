from __future__ import annotations

import sys
from abc import ABC, abstractmethod
from typing import TextIO

INTERVIEW_INPUT_TEXT = "text"
INTERVIEW_INPUT_VOICE = "voice"

SUPPORTED_INPUT_MODES = frozenset({INTERVIEW_INPUT_TEXT, INTERVIEW_INPUT_VOICE})

VOICE_FALLBACK_MESSAGE = (
    "Microphone or speech-to-text unavailable; falling back to text input."
)


class VoiceInputUnavailableError(RuntimeError):
    """Raised when a voice backend cannot capture spoken input."""


class VoiceInput(ABC):
    @abstractmethod
    def start(self) -> None:
        """Prepare the input backend for the interview."""

    @abstractmethod
    def listen(self) -> str:
        """Capture one spoken or typed utterance and return transcript text."""

    @abstractmethod
    def stop(self) -> None:
        """Release input resources after the interview."""

    @property
    def name(self) -> str:
        return self.__class__.__name__

    @property
    def is_available(self) -> bool:
        return True


class TextInput(VoiceInput):
    def __init__(
        self,
        *,
        stream: TextIO | None = None,
        input_stream: TextIO | None = None,
    ) -> None:
        self._stream = stream or sys.stdout
        self._input_stream = input_stream or sys.stdin
        self._started = False

    @property
    def name(self) -> str:
        return "text"

    def start(self) -> None:
        self._started = True

    def listen(self) -> str:
        if not self._started:
            self.start()
        return self._input_stream.readline().rstrip("\n")

    def stop(self) -> None:
        self._started = False


class OpenAIVoiceInput(VoiceInput):
    """Placeholder voice backend for future OpenAI speech-to-text integration."""

    def __init__(self, *, api_key: str | None = None) -> None:
        self._api_key = api_key
        self._started = False

    @property
    def name(self) -> str:
        return "openai_voice"

    @property
    def is_available(self) -> bool:
        return False

    def start(self) -> None:
        if not self.is_available:
            raise VoiceInputUnavailableError(
                "OpenAI voice input is not available in this prototype build."
            )
        self._started = True

    def listen(self) -> str:
        raise VoiceInputUnavailableError(
            "OpenAI voice input is not implemented yet."
        )

    def stop(self) -> None:
        self._started = False


def create_voice_input(
    mode: str,
    *,
    stream: TextIO | None = None,
    input_stream: TextIO | None = None,
    voice_backend: VoiceInput | None = None,
) -> tuple[VoiceInput, str | None]:
    if mode not in SUPPORTED_INPUT_MODES:
        raise ValueError(f"Unsupported interview input mode: {mode}")

    if mode == INTERVIEW_INPUT_TEXT:
        return TextInput(stream=stream, input_stream=input_stream), None

    voice_input = voice_backend
    if voice_input is None:
        from niros.local_voice_input import LocalVoiceInput

        voice_input = LocalVoiceInput(stream=stream)

    if voice_input.is_available:
        return voice_input, None

    return TextInput(stream=stream, input_stream=input_stream), VOICE_FALLBACK_MESSAGE
