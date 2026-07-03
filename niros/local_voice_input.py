from __future__ import annotations

import sys
from typing import Callable, TextIO

from niros.voice_input import VoiceInput, VoiceInputUnavailableError


def speech_recognition_importable() -> bool:
    try:
        import speech_recognition  # noqa: F401

        return True
    except ImportError:
        return False


def microphone_available() -> bool:
    if not speech_recognition_importable():
        return False
    try:
        import speech_recognition as sr

        return bool(sr.Microphone.list_microphone_names())
    except Exception:
        return False


def local_voice_input_available() -> bool:
    return speech_recognition_importable() and microphone_available()


Transcriber = Callable[[object, object], str]
ListenCapture = Callable[[], str]


def _default_listen_and_transcribe(
    *,
    stream: TextIO,
    recognizer: object,
    microphone_factory: Callable[[], object],
    transcriber: Transcriber,
    listen_timeout: float | None,
    phrase_time_limit: float | None,
) -> str:
    import speech_recognition as sr

    print("Listening... (speak now)", file=stream)
    with microphone_factory() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.3)
        audio = recognizer.listen(
            source,
            timeout=listen_timeout,
            phrase_time_limit=phrase_time_limit,
        )
    try:
        return transcriber(recognizer, audio)
    except sr.UnknownValueError:
        return ""
    except sr.RequestError as exc:
        raise VoiceInputUnavailableError(
            "Speech recognition service unavailable."
        ) from exc


def _default_transcriber(recognizer: object, audio: object) -> str:
    import speech_recognition as sr

    if hasattr(recognizer, "recognize_whisper"):
        try:
            return recognizer.recognize_whisper(audio)
        except (sr.UnknownValueError, sr.RequestError, OSError, AttributeError):
            pass

    return recognizer.recognize_google(audio)


class LocalVoiceInput(VoiceInput):
    """Local microphone input using speech_recognition for capture and transcription."""

    def __init__(
        self,
        *,
        stream: TextIO | None = None,
        recognizer: object | None = None,
        microphone_factory: Callable[[], object] | None = None,
        transcriber: Transcriber | None = None,
        listen_capture: ListenCapture | None = None,
        listen_timeout: float | None = None,
        phrase_time_limit: float | None = 15.0,
    ) -> None:
        self._stream = stream or sys.stdout
        self._listen_timeout = listen_timeout
        self._phrase_time_limit = phrase_time_limit
        self._listen_capture = listen_capture
        self._started = False
        self._recognizer = recognizer
        self._microphone_factory = microphone_factory
        self._transcriber = transcriber or _default_transcriber

    @property
    def name(self) -> str:
        return "local_voice"

    @property
    def is_available(self) -> bool:
        if self._listen_capture is not None:
            return True
        return local_voice_input_available()

    def start(self) -> None:
        if not self.is_available:
            raise VoiceInputUnavailableError(
                "Local voice input is unavailable. Check microphone and speech_recognition."
            )
        self._started = True

    def listen(self) -> str:
        if not self._started:
            self.start()

        if self._listen_capture is not None:
            transcript = self._listen_capture()
        else:
            recognizer = self._recognizer or self._build_recognizer()
            microphone_factory = self._microphone_factory or self._build_microphone_factory()
            transcript = _default_listen_and_transcribe(
                stream=self._stream,
                recognizer=recognizer,
                microphone_factory=microphone_factory,
                transcriber=self._transcriber,
                listen_timeout=self._listen_timeout,
                phrase_time_limit=self._phrase_time_limit,
            )

        print("Transcript:", file=self._stream)
        print(transcript, file=self._stream)
        return transcript

    def stop(self) -> None:
        self._started = False

    def _build_recognizer(self) -> object:
        import speech_recognition as sr

        return sr.Recognizer()

    def _build_microphone_factory(self) -> Callable[[], object]:
        import speech_recognition as sr

        return sr.Microphone
