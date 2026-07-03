import io

import pytest

from niros.assessment_runner import (
    AssessmentInputError,
    BIG_FIVE_SHORT_SECTION_TITLE,
    run_big_five_short_assessment,
)
from niros.assessments.big_five_short import get_big_five_short_items


class _WriteOnlyStream(io.StringIO):
    def readable(self) -> bool:
        return False


def test_reads_from_input_stream_not_output_stream():
    items = get_big_five_short_items()
    answers = "\n".join(["3"] * len(items)) + "\n"
    input_stream = io.StringIO(answers)
    output_stream = io.StringIO()

    results = run_big_five_short_assessment(
        language="en",
        input_stream=input_stream,
        output_stream=output_stream,
        print_output=True,
    )

    assert len(results) == 5
    assert BIG_FIVE_SHORT_SECTION_TITLE in output_stream.getvalue()
    assert "  Answer 1 (1-5):" in output_stream.getvalue()
    assert input_stream.read() == ""


def test_fake_preloaded_answers_skip_input_stream():
    answers = {item.id: 3 for item in get_big_five_short_items()}
    output_stream = io.StringIO()

    results = run_big_five_short_assessment(
        language="en",
        input_stream=_WriteOnlyStream(),
        output_stream=output_stream,
        answers=answers,
        print_output=True,
    )

    assert len(results) == 5
    assert "  Answer 1 (1-5):" not in output_stream.getvalue()


def test_invalid_value_retries_until_valid():
    items = get_big_five_short_items()
    lines = ["9", "0", "maybe", "3"] + ["3"] * (len(items) - 1)
    input_stream = io.StringIO("\n".join(lines) + "\n")
    output_stream = io.StringIO()

    results = run_big_five_short_assessment(
        language="en",
        input_stream=input_stream,
        output_stream=output_stream,
        print_output=True,
    )

    assert len(results) == 5
    rendered = output_stream.getvalue()
    assert rendered.count("Please enter a number from 1 to 5.") == 3


def test_unreadable_input_stream_raises_clear_error():
    with pytest.raises(AssessmentInputError, match="not readable"):
        run_big_five_short_assessment(
            language="en",
            input_stream=_WriteOnlyStream(),
            output_stream=io.StringIO(),
            print_output=False,
        )


def test_eof_raises_clear_error():
    input_stream = io.StringIO("")
    output_stream = io.StringIO()

    with pytest.raises(AssessmentInputError, match="ended before all questions"):
        run_big_five_short_assessment(
            language="en",
            input_stream=input_stream,
            output_stream=output_stream,
            print_output=False,
        )
