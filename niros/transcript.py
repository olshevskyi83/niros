from enum import Enum

from pydantic import BaseModel

from niros.models import SupportedLanguage


class InputModality(str, Enum):
    TEXT = "text"
    VOICE = "voice"


class Transcript(BaseModel):
    session_id: str
    raw_text: str
    input_modality: InputModality = InputModality.TEXT
    language: SupportedLanguage
    audio_ref: str | None = None
    voice_features: dict | None = None
