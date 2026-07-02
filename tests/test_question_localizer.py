from niros.question_localizer import localize_question


def test_english_returns_unchanged():
    question = "Tell me a little about yourself."

    assert localize_question(question, language="en") == question


def test_ukrainian_known_question():
    assert (
        localize_question("Tell me a little about yourself.", language="uk")
        == "Розкажіть трохи про себе."
    )


def test_russian_known_question():
    assert (
        localize_question("When do you feel most unclear about who you are?", language="ru")
        == "Когда вы сильнее всего чувствуете, что вам непонятно, кто вы?"
    )


def test_spanish_known_question():
    assert (
        localize_question(
            "What makes you feel like you probably cannot do this?",
            language="es",
        )
        == "¿Qué te hace sentir que probablemente no podrás hacerlo?"
    )


def test_unknown_question_returns_original():
    question = "What happens inside you when stress starts to build?"

    assert localize_question(question, language="uk") == question


def test_empty_string_returns_empty_string():
    assert localize_question("", language="uk") == ""


def test_whitespace_is_trimmed():
    question = "  Tell me a little about yourself.  "

    assert localize_question(question, language="en") == "Tell me a little about yourself."


def test_ukrainian_fallback_question():
    assert (
        localize_question("Tell me what brought you here today.", language="uk")
        == "Розкажіть, що привело вас сюди сьогодні."
    )


def test_russian_fallback_question():
    assert (
        localize_question("Tell me what brought you here today.", language="ru")
        == "Расскажите, что привело вас сюда сегодня."
    )


def test_spanish_fallback_question():
    assert (
        localize_question("Tell me what brought you here today.", language="es")
        == "Cuéntame qué te trajo aquí hoy."
    )
