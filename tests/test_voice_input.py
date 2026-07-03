import io
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT / "scripts"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(SCRIPTS_DIR))

from demo_interview import read_answer, run_demo
from niros.local_voice_input import LocalVoiceInput, local_voice_input_available
from niros.voice_input import (
    INTERVIEW_INPUT_TEXT,
    INTERVIEW_INPUT_VOICE,
    VOICE_FALLBACK_MESSAGE,
    OpenAIVoiceInput,
    TextInput,
    VoiceInput,
    VoiceInputUnavailableError,
    create_voice_input,
)
from run_niros import run_niros


def test_voice_input_abstraction_contract():
    adapter = TextInput(
        stream=io.StringIO(),
        input_stream=io.StringIO("hello world\n"),
    )

    adapter.start()
    assert adapter.is_available is True
    assert adapter.listen() == "hello world"
    adapter.stop()


def test_text_input_implements_voice_input_interface():
    assert issubclass(TextInput, VoiceInput)


def test_local_voice_input_with_fake_transcript():
    output = io.StringIO()
    voice = LocalVoiceInput(
        stream=output,
        listen_capture=lambda: "spoken answer from microphone",
    )

    voice.start()
    transcript = voice.listen()
    voice.stop()

    assert transcript == "spoken answer from microphone"
    assert "Transcript:" in output.getvalue()
    assert "spoken answer from microphone" in output.getvalue()


def test_local_voice_input_fake_capture_is_available_without_hardware():
    voice = LocalVoiceInput(listen_capture=lambda: "test")

    assert voice.is_available is True


def test_openai_voice_input_is_placeholder_only():
    voice = OpenAIVoiceInput()

    assert voice.is_available is False
    assert voice.name == "openai_voice"

    with pytest.raises(VoiceInputUnavailableError):
        voice.start()

    with pytest.raises(VoiceInputUnavailableError):
        voice.listen()


def test_create_voice_input_text_mode():
    adapter, message = create_voice_input(
        INTERVIEW_INPUT_TEXT,
        stream=io.StringIO(),
        input_stream=io.StringIO(),
    )

    assert isinstance(adapter, TextInput)
    assert message is None


def test_create_voice_input_voice_mode_falls_back_to_text():
    adapter, message = create_voice_input(
        INTERVIEW_INPUT_VOICE,
        stream=io.StringIO(),
        input_stream=io.StringIO(),
    )

    assert isinstance(adapter, TextInput)
    assert message == VOICE_FALLBACK_MESSAGE


def test_create_voice_input_voice_mode_uses_injected_backend():
    backend = LocalVoiceInput(listen_capture=lambda: "injected")
    adapter, message = create_voice_input(
        INTERVIEW_INPUT_VOICE,
        stream=io.StringIO(),
        voice_backend=backend,
    )

    assert adapter is backend
    assert message is None


def test_read_answer_uses_text_input_adapter():
    output = io.StringIO()
    answer = read_answer(
        None,
        1,
        output,
        voice_input=TextInput(
            stream=output,
            input_stream=io.StringIO("typed answer\n"),
        ),
    )

    assert answer == "typed answer"
    assert "You (turn 1):" in output.getvalue()


def test_read_answer_voice_prints_transcript_before_return():
    output = io.StringIO()
    answer = read_answer(
        None,
        1,
        output,
        voice_input=LocalVoiceInput(
            stream=output,
            listen_capture=lambda: "voice transcript",
        ),
    )

    assert answer == "voice transcript"
    rendered = output.getvalue()
    assert "You (turn 1):" not in rendered
    assert "Transcript:" in rendered
    assert "voice transcript" in rendered


def test_create_voice_input_voice_fallback_is_used_by_read_answer():
    output = io.StringIO()
    adapter, message = create_voice_input(
        INTERVIEW_INPUT_VOICE,
        stream=output,
        input_stream=io.StringIO("voice fallback answer\n"),
    )

    assert message is not None
    answer = read_answer(None, 1, output, voice_input=adapter)

    assert answer == "voice fallback answer"


def test_read_answer_prefers_planned_input_over_voice_adapter():
    output = io.StringIO()
    answer = read_answer(
        "planned answer",
        1,
        output,
        voice_input=LocalVoiceInput(
            stream=output,
            listen_capture=lambda: "ignored",
        ),
    )

    assert answer == "planned answer"
    assert output.getvalue() == ""


def test_run_niros_voice_mode_falls_back_and_completes(monkeypatch):
    output = io.StringIO()
    monkeypatch.setattr(
        "niros.local_voice_input.local_voice_input_available",
        lambda: False,
    )
    monkeypatch.setattr(
        "sys.stdin",
        io.StringIO("I worry people will stop liking me.\n"),
    )

    exit_code = run_niros(
        turns=1,
        provider="mock",
        output_stream=output,
        input_mode=INTERVIEW_INPUT_VOICE,
    )

    rendered = output.getvalue()

    assert exit_code == 0
    assert VOICE_FALLBACK_MESSAGE in rendered
    assert "Human Profile Summary" in rendered


def test_run_niros_text_mode_still_works():
    output = io.StringIO()

    exit_code = run_niros(
        user_inputs=[
            "I feel anxious when people become distant.",
            "I try to make everyone happy.",
            "My mind gets stuck on the same worries.",
        ],
        turns=3,
        provider="mock",
        output_stream=output,
        input_mode=INTERVIEW_INPUT_TEXT,
    )

    rendered = output.getvalue()

    assert exit_code == 0
    assert "Interview input: text" in rendered
    assert VOICE_FALLBACK_MESSAGE not in rendered
    assert "Scenario Blueprint" in rendered


def test_run_demo_text_mode_with_planned_inputs():
    output = io.StringIO()

    exit_code = run_demo(
        user_inputs=["I stay quiet even when I disagree."],
        turns=1,
        provider="mock",
        output_stream=output,
        input_mode=INTERVIEW_INPUT_TEXT,
    )

    assert exit_code == 0
    assert "Interview input: text" in output.getvalue()


def test_local_voice_input_availability_matches_helper(monkeypatch):
    monkeypatch.setattr(
        "niros.local_voice_input.local_voice_input_available",
        lambda: False,
    )
    voice = LocalVoiceInput()

    assert voice.is_available is False
    assert local_voice_input_available() is False
