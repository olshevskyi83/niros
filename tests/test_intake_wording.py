from niros.intake_protocol import CURRENT_IMPACT_ID, DEFAULT_INTAKE_PROTOCOL

OLD_Q4_PHRASES = {
    "en": "What is this problem interfering with most in your life right now?",
    "uk": "Що зараз найбільше заважає вам у житті через цю проблему?",
    "ru": "Что сейчас больше всего мешает вам в жизни из-за этой проблемы?",
    "es": "¿En qué te está afectando más este problema ahora?",
}

NEW_Q4_PHRASES = {
    "en": "How is this problem affecting your life right now?",
    "uk": "Як ця проблема зараз найбільше впливає на ваше життя?",
    "ru": "Как эта проблема сейчас больше всего влияет на вашу жизнь?",
    "es": "¿Cómo está afectando este problema a tu vida ahora?",
}


def test_q4_wording_updated_in_all_languages():
    for language, expected in NEW_Q4_PHRASES.items():
        text = DEFAULT_INTAKE_PROTOCOL.question_text(CURRENT_IMPACT_ID, language)
        assert text == expected


def test_old_awkward_q4_wording_no_longer_appears():
    for language, old_text in OLD_Q4_PHRASES.items():
        text = DEFAULT_INTAKE_PROTOCOL.question_text(CURRENT_IMPACT_ID, language)
        assert old_text not in text
        assert text != old_text
