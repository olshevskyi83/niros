#!/usr/bin/env python3
"""Generate evaluation/psychedelic_intake_matrix.yaml for multilingual intake testing."""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "evaluation" / "psychedelic_intake_matrix.yaml"

# Each entry: (domain_key, language, input, facts, patterns, negatives)
CASE_SPECS: list[tuple[str, str, str, list[dict], list[str], list[str]]] = [
    # Domain 1 — Low mood / depression-like (uk)
    ("mood", "uk", "мій настрій більшість днів низький", [{"category": "emotion", "attribute": "reported_low_mood", "value": "present"}], ["low_mood_signal", "depressed_mood_signal"], ["fibromyalgia_signal", "stuttering_signal"]),
    ("mood", "uk", "я відчуваю депресію", [{"category": "emotion", "attribute": "reported_low_mood", "value": "present"}], ["depressed_mood_signal", "emotional_distress_signal"], ["perfectionism", "rumination"]),
    ("mood", "uk", "нічого не приносить мені радості", [{"category": "emotion", "attribute": "reported_low_mood", "value": "present"}], ["anhedonia_signal", "low_mood_signal"], ["speech_anxiety", "mystical_expectation"]),
    ("mood", "uk", "надія здається далекою", [{"category": "self", "attribute": "perceived_helplessness", "value": "present"}], ["hopelessness_signal", "loss_of_meaning"], ["spiritual_openness", "fatigue_burden"]),
    ("mood", "uk", "відчуваю важкість і пригніченість", [{"category": "emotion", "attribute": "reported_distress", "value": "present"}], ["emotional_heaviness", "depressed_mood_signal"], ["fear_of_bad_trip", "hypervigilance"]),
    ("mood", "uk", "життя здається meaningless", [{"category": "meaning", "attribute": "meaning_sense", "value": "unclear"}], ["loss_of_meaning", "hopelessness_signal"], ["speech_anxiety", "chronic_pain_burden"]),
    # Domain 2 — Anxiety / fear (uk)
    ("anxiety", "uk", "мені страшно без причини", [{"category": "emotion", "attribute": "reported_fear", "value": "present"}], ["generalized_fear", "emotional_distress_signal"], ["meaning_seeking", "integration_need"]),
    ("anxiety", "uk", "я боюся втратити контроль", [{"category": "emotion", "attribute": "reported_fear", "value": "elevated"}], ["fear_of_losing_control", "panic_reactivity"], ["spiritual_openness", "anhedonia_signal"]),
    ("anxiety", "uk", "я боюся смерті", [{"category": "emotion", "attribute": "reported_fear", "value": "elevated"}], ["fear_of_death", "existential_fear"], ["stuttering_signal", "people_pleasing"]),
    ("anxiety", "uk", "я завжди у стресі", [{"category": "emotion", "attribute": "chronic_stress", "value": "present"}], ["chronic_stress_signal", "emotional_distress_signal"], ["mystical_expectation", "trust_difficulty"]),
    ("anxiety", "uk", "тривога відчувається в тілі", [{"category": "emotion", "attribute": "reported_distress", "value": "present"}], ["somatic_anxiety", "generalized_fear"], ["loss_of_meaning", "communication_avoidance"]),
    # Domain 3 — Trauma / stress (uk)
    ("trauma", "uk", "я постійно напоготові", [{"category": "trauma", "attribute": "trauma_stress", "value": "present"}], ["hypervigilance", "startle_sensitivity"], ["spiritual_openness", "anhedonia_signal"]),
    ("trauma", "uk", "повертаються небажані спогади", [{"category": "trauma", "attribute": "trauma_stress", "value": "present"}], ["intrusive_memories", "hypervigilance"], ["meaning_seeking", "fatigue_burden"]),
    ("trauma", "uk", "я уникаю тригерів", [{"category": "trauma", "attribute": "trauma_stress", "value": "present"}], ["avoidance_of_triggers", "hypervigilance"], ["spiritual_openness", "low_mood_signal"]),
    ("trauma", "uk", "я ніби відключений від емоцій", [{"category": "emotion", "attribute": "reported_distress", "value": "reduced"}], ["emotional_numbing", "dissociation_signal"], ["speech_anxiety", "mystical_expectation"]),
    # Domain 4 — Shame / self-worth (uk)
    ("shame", "uk", "мені соромно, коли мене критикують", [{"category": "emotion", "attribute": "reported_distress", "value": "present"}], ["shame_sensitivity", "harsh_self_criticism"], ["fibromyalgia_signal", "spiritual_openness"]),
    ("shame", "uk", "я постійно себе критикую", [{"category": "self", "attribute": "self_worth", "value": "unstable"}], ["harsh_self_criticism", "self_worth_instability"], ["fear_of_bad_trip", "sleep_disruption"]),
    ("shame", "uk", "відчуваю провину за минуле", [{"category": "emotion", "attribute": "reported_distress", "value": "present"}], ["guilt_burden", "shame_sensitivity"], ["stuttering_signal", "meaning_seeking"]),
    ("shame", "uk", "я відчуваю себе unworthy", [{"category": "self", "attribute": "self_worth", "value": "low"}], ["unworthiness_signal", "self_worth_instability"], ["chronic_pain_burden", "spiritual_resistance"]),
    # Domain 5 — Rumination (uk)
    ("rumination", "uk", "мій розум застрягає на тих самих думках", [{"category": "emotion", "attribute": "reported_distress", "value": "present"}], ["rumination", "obsessive_thinking_loop"], ["spiritual_openness", "fibromyalgia_signal"]),
    ("rumination", "uk", "я постійно все контролюю в голові", [{"category": "emotion", "attribute": "reported_distress", "value": "elevated"}], ["mental_overcontrol", "rumination"], ["anhedonia_signal", "trust_in_facilitator_difficulty"]),
    ("rumination", "uk", "не можу відпустити ці думки", [{"category": "emotion", "attribute": "reported_distress", "value": "present"}], ["inability_to_let_go", "rumination"], ["fatigue_burden", "mystical_expectation"]),
    # Domain 6 — Body (uk)
    ("body", "uk", "живу з фіброміалгією", [{"category": "body", "attribute": "pain_burden", "value": "present"}], ["fibromyalgia_signal", "chronic_pain_burden"], ["speech_anxiety", "spiritual_openness"]),
    ("body", "uk", "я постійно втомлений", [{"category": "body", "attribute": "reported_fatigue", "value": "present"}], ["fatigue_burden", "chronic_pain_burden"], ["fear_of_speaking", "meaning_seeking"]),
    ("body", "uk", "моє тіло постійно болить", [{"category": "body", "attribute": "pain_burden", "value": "present"}], ["chronic_pain_burden", "body_sensitivity"], ["rumination", "psychedelic_anxiety"]),
    ("body", "uk", "біль викликає страх", [{"category": "body", "attribute": "pain_burden", "value": "present"}, {"category": "emotion", "attribute": "reported_fear", "value": "present"}], ["pain_fear_cycle", "chronic_pain_burden"], ["spiritual_openness", "anhedonia_signal"]),
    ("body", "uk", "симптоми непередбачувані", [{"category": "body", "attribute": "pain_burden", "value": "present"}], ["symptom_unpredictability", "fibromyalgia_signal"], ["meaning_seeking", "trust_difficulty"]),
    ("body", "uk", "сон порушений", [{"category": "sleep", "attribute": "nightmares", "value": "present"}], ["sleep_disruption", "nightmare_disturbance"], ["spiritual_openness", "speech_anxiety"]),
    # Domain 7 — Speech (uk)
    ("speech", "uk", "я заїкаюсь", [{"category": "speech", "attribute": "stuttering", "value": "present"}], ["stuttering_signal", "speech_anxiety"], ["fibromyalgia_signal", "loss_of_meaning"]),
    ("speech", "uk", "боюся говорити з людьми", [{"category": "speech", "attribute": "speech_comfort", "value": "reduced"}], ["fear_of_speaking", "communication_avoidance"], ["chronic_pain_burden", "mystical_expectation"]),
    ("speech", "uk", "соромно говорити", [{"category": "speech", "attribute": "speech_comfort", "value": "reduced"}], ["shame_about_speech", "speech_anxiety"], ["fatigue_burden", "spiritual_openness"]),
    ("speech", "uk", "важко висловити себе", [{"category": "speech", "attribute": "speech_comfort", "value": "blocked"}], ["self_expression_block", "communication_avoidance"], ["fear_of_death", "integration_need"]),
    # Domain 8 — Psychedelic (uk)
    ("psychedelic", "uk", "я боюся поганого тріпу", [{"category": "session", "attribute": "fear_of_bad_trip", "value": "present"}], ["fear_of_bad_trip", "psychedelic_anxiety"], ["fatigue_burden", "people_pleasing"]),
    ("psychedelic", "uk", "важко відпустити контроль на сесії", [{"category": "session", "attribute": "session_openness", "value": "resistant"}], ["surrender_difficulty", "control_resistance"], ["low_mood_signal", "chronic_pain_burden"]),
    ("psychedelic", "uk", "боюся відчуттів у тілі під час сесії", [{"category": "emotion", "attribute": "reported_fear", "value": "elevated"}], ["fear_of_body_sensations", "psychedelic_anxiety"], ["meaning_seeking", "stuttering_signal"]),
    ("psychedelic", "uk", "важко довіряти фасилітатору", [{"category": "relationship", "attribute": "trust", "value": "low"}], ["trust_in_facilitator_difficulty", "psychedelic_anxiety"], ["spiritual_openness", "anhedonia_signal"]),
    ("psychedelic", "uk", "потрібна інтеграція після досвіду", [{"category": "meaning", "attribute": "change_desire", "value": "seeking"}], ["integration_need", "meaning_seeking"], ["stuttering_signal", "panic_reactivity"]),
    # Domain 9 — Spirituality (uk)
    ("spirituality", "uk", "я відкритий до духовного досвіду", [{"category": "meaning", "attribute": "meaning_sense", "value": "seeking"}], ["spiritual_openness", "meaning_seeking"], ["fear_of_bad_trip", "harsh_self_criticism"]),
    ("spirituality", "uk", "я опираюся духовному досвіду", [{"category": "meaning", "attribute": "change_desire", "value": "resistant"}], ["spiritual_resistance", "control_resistance"], ["anhedonia_signal", "fibromyalgia_signal"]),
    ("spirituality", "uk", "шукаю sense of meaning", [{"category": "meaning", "attribute": "meaning_sense", "value": "seeking"}], ["meaning_seeking", "desire_for_change"], ["stuttering_signal", "pain_fear_cycle"]),
    ("spirituality", "uk", "очікую містичний досвід", [{"category": "meaning", "attribute": "change_desire", "value": "seeking"}], ["mystical_expectation", "spiritual_openness"], ["guilt_burden", "communication_avoidance"]),
    ("spirituality", "uk", "я боюся жити", [{"category": "emotion", "attribute": "reported_fear", "value": "elevated"}], ["existential_fear", "safety_concern_signal"], ["perfectionism", "fibromyalgia_signal"]),
]

# English cases (22)
CASE_SPECS.extend([
    ("mood", "en", "my mood stays low most days", [{"category": "emotion", "attribute": "reported_low_mood", "value": "present"}], ["low_mood_signal", "depressed_mood_signal"], ["fibromyalgia_signal", "stuttering_signal"]),
    ("mood", "en", "I feel depressed", [{"category": "emotion", "attribute": "reported_low_mood", "value": "present"}], ["depressed_mood_signal", "emotional_distress_signal"], ["perfectionism", "rumination"]),
    ("mood", "en", "nothing really brings me joy lately", [{"category": "emotion", "attribute": "reported_low_mood", "value": "present"}], ["anhedonia_signal", "low_mood_signal"], ["speech_anxiety", "mystical_expectation"]),
    ("mood", "en", "hope feels far away", [{"category": "self", "attribute": "perceived_helplessness", "value": "present"}], ["hopelessness_signal", "loss_of_meaning"], ["spiritual_openness", "fatigue_burden"]),
    ("mood", "en", "I feel heavy and weighed down", [{"category": "emotion", "attribute": "reported_distress", "value": "present"}], ["emotional_heaviness", "depressed_mood_signal"], ["fear_of_bad_trip", "hypervigilance"]),
    ("anxiety", "en", "I feel scared and I don't know why", [{"category": "emotion", "attribute": "reported_fear", "value": "present"}], ["generalized_fear", "emotional_distress_signal"], ["meaning_seeking", "integration_need"]),
    ("anxiety", "en", "I'm afraid of losing control", [{"category": "emotion", "attribute": "reported_fear", "value": "elevated"}], ["fear_of_losing_control", "panic_reactivity"], ["spiritual_openness", "anhedonia_signal"]),
    ("anxiety", "en", "I'm afraid of death", [{"category": "emotion", "attribute": "reported_fear", "value": "elevated"}], ["fear_of_death", "existential_fear"], ["stuttering_signal", "people_pleasing"]),
    ("anxiety", "en", "I'm always stressed", [{"category": "emotion", "attribute": "chronic_stress", "value": "present"}], ["chronic_stress_signal", "emotional_distress_signal"], ["mystical_expectation", "trust_difficulty"]),
    ("anxiety", "en", "anxiety lives in my body", [{"category": "emotion", "attribute": "reported_distress", "value": "present"}], ["somatic_anxiety", "generalized_fear"], ["loss_of_meaning", "communication_avoidance"]),
    ("trauma", "en", "I'm constantly on guard", [{"category": "trauma", "attribute": "trauma_stress", "value": "present"}], ["hypervigilance", "startle_sensitivity"], ["spiritual_openness", "anhedonia_signal"]),
    ("trauma", "en", "unwanted memories keep coming back", [{"category": "trauma", "attribute": "trauma_stress", "value": "present"}], ["intrusive_memories", "hypervigilance"], ["meaning_seeking", "fatigue_burden"]),
    ("trauma", "en", "I avoid triggers when I can", [{"category": "trauma", "attribute": "trauma_stress", "value": "present"}], ["avoidance_of_triggers", "hypervigilance"], ["spiritual_openness", "low_mood_signal"]),
    ("shame", "en", "I feel ashamed when someone criticizes me", [{"category": "emotion", "attribute": "reported_distress", "value": "present"}], ["shame_sensitivity", "harsh_self_criticism"], ["fibromyalgia_signal", "spiritual_openness"]),
    ("shame", "en", "I attack myself internally after mistakes", [{"category": "self", "attribute": "self_worth", "value": "unstable"}], ["harsh_self_criticism", "self_worth_instability"], ["fear_of_bad_trip", "sleep_disruption"]),
    ("rumination", "en", "My mind gets stuck on the same worries", [{"category": "emotion", "attribute": "reported_distress", "value": "present"}], ["rumination", "obsessive_thinking_loop"], ["spiritual_openness", "fibromyalgia_signal"]),
    ("rumination", "en", "I can't let go of these thoughts", [{"category": "emotion", "attribute": "reported_distress", "value": "present"}], ["inability_to_let_go", "rumination"], ["fatigue_burden", "mystical_expectation"]),
    ("body", "en", "I live with fibromyalgia", [{"category": "body", "attribute": "pain_burden", "value": "present"}], ["fibromyalgia_signal", "chronic_pain_burden"], ["speech_anxiety", "spiritual_openness"]),
    ("body", "en", "I'm exhausted all the time", [{"category": "body", "attribute": "reported_fatigue", "value": "present"}], ["fatigue_burden", "chronic_pain_burden"], ["fear_of_speaking", "meaning_seeking"]),
    ("body", "en", "my body hurts all the time", [{"category": "body", "attribute": "pain_burden", "value": "present"}], ["chronic_pain_burden", "body_sensitivity"], ["rumination", "psychedelic_anxiety"]),
    ("speech", "en", "I stutter when I speak", [{"category": "speech", "attribute": "stuttering", "value": "present"}], ["stuttering_signal", "speech_anxiety"], ["fibromyalgia_signal", "loss_of_meaning"]),
    ("speech", "en", "I'm afraid to speak in front of people", [{"category": "speech", "attribute": "speech_comfort", "value": "reduced"}], ["fear_of_speaking", "communication_avoidance"], ["chronic_pain_burden", "mystical_expectation"]),
    ("psychedelic", "en", "I'm afraid of a bad trip", [{"category": "session", "attribute": "fear_of_bad_trip", "value": "present"}], ["fear_of_bad_trip", "psychedelic_anxiety"], ["fatigue_burden", "people_pleasing"]),
    ("psychedelic", "en", "I find it hard to surrender during the session", [{"category": "session", "attribute": "session_openness", "value": "resistant"}], ["surrender_difficulty", "control_resistance"], ["low_mood_signal", "chronic_pain_burden"]),
    ("psychedelic", "en", "I need help integrating the experience", [{"category": "meaning", "attribute": "change_desire", "value": "seeking"}], ["integration_need", "meaning_seeking"], ["stuttering_signal", "panic_reactivity"]),
    ("spirituality", "en", "I'm open to a spiritual experience", [{"category": "meaning", "attribute": "meaning_sense", "value": "seeking"}], ["spiritual_openness", "meaning_seeking"], ["fear_of_bad_trip", "harsh_self_criticism"]),
    ("spirituality", "en", "I'm searching for meaning", [{"category": "meaning", "attribute": "meaning_sense", "value": "seeking"}], ["meaning_seeking", "desire_for_change"], ["stuttering_signal", "pain_fear_cycle"]),
    ("spirituality", "en", "I'm afraid to live", [{"category": "emotion", "attribute": "reported_fear", "value": "elevated"}], ["existential_fear", "safety_concern_signal"], ["perfectionism", "fibromyalgia_signal"]),
])

# Russian cases (22) - use ru typical phrases
CASE_SPECS.extend([
    ("mood", "ru", "моё настроение большую часть дней низкое", [{"category": "emotion", "attribute": "reported_low_mood", "value": "present"}], ["low_mood_signal", "depressed_mood_signal"], ["fibromyalgia_signal", "stuttering_signal"]),
    ("mood", "ru", "я чувствую депрессию", [{"category": "emotion", "attribute": "reported_low_mood", "value": "present"}], ["depressed_mood_signal", "emotional_distress_signal"], ["perfectionism", "rumination"]),
    ("mood", "ru", "ничто не приносит мне радости", [{"category": "emotion", "attribute": "reported_low_mood", "value": "present"}], ["anhedonia_signal", "low_mood_signal"], ["speech_anxiety", "mystical_expectation"]),
    ("mood", "ru", "надежда кажется далёкой", [{"category": "self", "attribute": "perceived_helplessness", "value": "present"}], ["hopelessness_signal", "loss_of_meaning"], ["spiritual_openness", "fatigue_burden"]),
    ("anxiety", "ru", "мне страшно без причины", [{"category": "emotion", "attribute": "reported_fear", "value": "present"}], ["generalized_fear", "emotional_distress_signal"], ["meaning_seeking", "integration_need"]),
    ("anxiety", "ru", "я боюсь потерять контроль", [{"category": "emotion", "attribute": "reported_fear", "value": "elevated"}], ["fear_of_losing_control", "panic_reactivity"], ["spiritual_openness", "anhedonia_signal"]),
    ("anxiety", "ru", "я боюсь смерти", [{"category": "emotion", "attribute": "reported_fear", "value": "elevated"}], ["fear_of_death", "existential_fear"], ["stuttering_signal", "people_pleasing"]),
    ("anxiety", "ru", "я всегда в стрессе", [{"category": "emotion", "attribute": "chronic_stress", "value": "present"}], ["chronic_stress_signal", "emotional_distress_signal"], ["mystical_expectation", "trust_difficulty"]),
    ("trauma", "ru", "я постоянно настороже", [{"category": "trauma", "attribute": "trauma_stress", "value": "present"}], ["hypervigilance", "startle_sensitivity"], ["spiritual_openness", "anhedonia_signal"]),
    ("trauma", "ru", "возвращаются нежелательные воспоминания", [{"category": "trauma", "attribute": "trauma_stress", "value": "present"}], ["intrusive_memories", "hypervigilance"], ["meaning_seeking", "fatigue_burden"]),
    ("shame", "ru", "мне стыдно, когда меня критикуют", [{"category": "emotion", "attribute": "reported_distress", "value": "present"}], ["shame_sensitivity", "harsh_self_criticism"], ["fibromyalgia_signal", "spiritual_openness"]),
    ("shame", "ru", "я чувствую себя unworthy", [{"category": "self", "attribute": "self_worth", "value": "low"}], ["unworthiness_signal", "self_worth_instability"], ["chronic_pain_burden", "spiritual_resistance"]),
    ("rumination", "ru", "мой ум застревает на одних и тех же переживаниях", [{"category": "emotion", "attribute": "reported_distress", "value": "present"}], ["rumination", "obsessive_thinking_loop"], ["spiritual_openness", "fibromyalgia_signal"]),
    ("rumination", "ru", "не могу отпустить эти мысли", [{"category": "emotion", "attribute": "reported_distress", "value": "present"}], ["inability_to_let_go", "rumination"], ["fatigue_burden", "mystical_expectation"]),
    ("body", "ru", "живу с фибромиалгией", [{"category": "body", "attribute": "pain_burden", "value": "present"}], ["fibromyalgia_signal", "chronic_pain_burden"], ["speech_anxiety", "spiritual_openness"]),
    ("body", "ru", "я постоянно exhausted", [{"category": "body", "attribute": "reported_fatigue", "value": "present"}], ["fatigue_burden", "chronic_pain_burden"], ["fear_of_speaking", "meaning_seeking"]),
    ("body", "ru", "моё тело постоянно болит", [{"category": "body", "attribute": "pain_burden", "value": "present"}], ["chronic_pain_burden", "body_sensitivity"], ["rumination", "psychedelic_anxiety"]),
    ("speech", "ru", "я заикаюсь, когда говорю", [{"category": "speech", "attribute": "stuttering", "value": "present"}], ["stuttering_signal", "speech_anxiety"], ["fibromyalgia_signal", "loss_of_meaning"]),
    ("speech", "ru", "мне тревожно, когда нужно говорить", [{"category": "speech", "attribute": "speech_comfort", "value": "reduced"}], ["fear_of_speaking", "speech_anxiety"], ["chronic_pain_burden", "mystical_expectation"]),
    ("psychedelic", "ru", "я боюсь bad trip", [{"category": "session", "attribute": "fear_of_bad_trip", "value": "present"}], ["fear_of_bad_trip", "psychedelic_anxiety"], ["fatigue_burden", "people_pleasing"]),
    ("psychedelic", "ru", "мне нужна интеграция опыта", [{"category": "meaning", "attribute": "change_desire", "value": "seeking"}], ["integration_need", "meaning_seeking"], ["stuttering_signal", "panic_reactivity"]),
    ("spirituality", "ru", "я боюсь жить", [{"category": "emotion", "attribute": "reported_fear", "value": "elevated"}], ["existential_fear", "safety_concern_signal"], ["perfectionism", "fibromyalgia_signal"]),
    ("spirituality", "ru", "я ищу sense of meaning", [{"category": "meaning", "attribute": "meaning_sense", "value": "seeking"}], ["meaning_seeking", "desire_for_change"], ["stuttering_signal", "pain_fear_cycle"]),
])

# Spanish cases (22)
CASE_SPECS.extend([
    ("mood", "es", "mi ánimo se mantiene bajo la mayoría de los días", [{"category": "emotion", "attribute": "reported_low_mood", "value": "present"}], ["low_mood_signal", "depressed_mood_signal"], ["fibromyalgia_signal", "stuttering_signal"]),
    ("mood", "es", "me siento deprimido", [{"category": "emotion", "attribute": "reported_low_mood", "value": "present"}], ["depressed_mood_signal", "emotional_distress_signal"], ["perfectionism", "rumination"]),
    ("mood", "es", "nada me trae alegría últimamente", [{"category": "emotion", "attribute": "reported_low_mood", "value": "present"}], ["anhedonia_signal", "low_mood_signal"], ["speech_anxiety", "mystical_expectation"]),
    ("mood", "es", "la esperanza se siente lejana", [{"category": "self", "attribute": "perceived_helplessness", "value": "present"}], ["hopelessness_signal", "loss_of_meaning"], ["spiritual_openness", "fatigue_burden"]),
    ("anxiety", "es", "tengo miedo sin saber por qué", [{"category": "emotion", "attribute": "reported_fear", "value": "present"}], ["generalized_fear", "emotional_distress_signal"], ["meaning_seeking", "integration_need"]),
    ("anxiety", "es", "tengo miedo de perder el control", [{"category": "emotion", "attribute": "reported_fear", "value": "elevated"}], ["fear_of_losing_control", "panic_reactivity"], ["spiritual_openness", "anhedonia_signal"]),
    ("anxiety", "es", "tengo miedo a la muerte", [{"category": "emotion", "attribute": "reported_fear", "value": "elevated"}], ["fear_of_death", "existential_fear"], ["stuttering_signal", "people_pleasing"]),
    ("anxiety", "es", "siempre estoy estresado", [{"category": "emotion", "attribute": "chronic_stress", "value": "present"}], ["chronic_stress_signal", "emotional_distress_signal"], ["mystical_expectation", "trust_difficulty"]),
    ("trauma", "es", "estoy constantemente alerta", [{"category": "trauma", "attribute": "trauma_stress", "value": "present"}], ["hypervigilance", "startle_sensitivity"], ["spiritual_openness", "anhedonia_signal"]),
    ("trauma", "es", "vuelven recuerdos no deseados", [{"category": "trauma", "attribute": "trauma_stress", "value": "present"}], ["intrusive_memories", "hypervigilance"], ["meaning_seeking", "fatigue_burden"]),
    ("shame", "es", "me siento avergonzado cuando me critican", [{"category": "emotion", "attribute": "reported_distress", "value": "present"}], ["shame_sensitivity", "harsh_self_criticism"], ["fibromyalgia_signal", "spiritual_openness"]),
    ("shame", "es", "me siento indigno", [{"category": "self", "attribute": "self_worth", "value": "low"}], ["unworthiness_signal", "self_worth_instability"], ["chronic_pain_burden", "spiritual_resistance"]),
    ("rumination", "es", "mi mente se queda atascada en las mismas preocupaciones", [{"category": "emotion", "attribute": "reported_distress", "value": "present"}], ["rumination", "obsessive_thinking_loop"], ["spiritual_openness", "fibromyalgia_signal"]),
    ("rumination", "es", "no puedo soltar estos pensamientos", [{"category": "emotion", "attribute": "reported_distress", "value": "present"}], ["inability_to_let_go", "rumination"], ["fatigue_burden", "mystical_expectation"]),
    ("body", "es", "vivo con fibromialgia", [{"category": "body", "attribute": "pain_burden", "value": "present"}], ["fibromyalgia_signal", "chronic_pain_burden"], ["speech_anxiety", "spiritual_openness"]),
    ("body", "es", "estoy agotado todo el tiempo", [{"category": "body", "attribute": "reported_fatigue", "value": "present"}], ["fatigue_burden", "chronic_pain_burden"], ["fear_of_speaking", "meaning_seeking"]),
    ("body", "es", "mi cuerpo duele todo el tiempo", [{"category": "body", "attribute": "pain_burden", "value": "present"}], ["chronic_pain_burden", "body_sensitivity"], ["rumination", "psychedelic_anxiety"]),
    ("speech", "es", "tartamudeo cuando hablo", [{"category": "speech", "attribute": "stuttering", "value": "present"}], ["stuttering_signal", "speech_anxiety"], ["fibromyalgia_signal", "loss_of_meaning"]),
    ("speech", "es", "me pongo ansioso cuando tengo que hablar", [{"category": "speech", "attribute": "speech_comfort", "value": "reduced"}], ["fear_of_speaking", "speech_anxiety"], ["chronic_pain_burden", "mystical_expectation"]),
    ("psychedelic", "es", "tengo miedo de un mal viaje", [{"category": "session", "attribute": "fear_of_bad_trip", "value": "present"}], ["fear_of_bad_trip", "psychedelic_anxiety"], ["fatigue_burden", "people_pleasing"]),
    ("psychedelic", "es", "necesito ayuda para integrar la experiencia", [{"category": "meaning", "attribute": "change_desire", "value": "seeking"}], ["integration_need", "meaning_seeking"], ["stuttering_signal", "panic_reactivity"]),
    ("spirituality", "es", "tengo miedo de vivir", [{"category": "emotion", "attribute": "reported_fear", "value": "elevated"}], ["existential_fear", "safety_concern_signal"], ["perfectionism", "fibromyalgia_signal"]),
    ("spirituality", "es", "busco sentido en la vida", [{"category": "meaning", "attribute": "meaning_sense", "value": "seeking"}], ["meaning_seeking", "desire_for_change"], ["stuttering_signal", "pain_fear_cycle"]),
])


def build_cases() -> list[dict]:
    counters: dict[tuple[str, str], int] = {}
    cases: list[dict] = []

    for domain, language, input_text, facts, patterns, negatives in CASE_SPECS:
        key = (language, domain)
        counters[key] = counters.get(key, 0) + 1
        case_id = f"{language}_{domain}_{counters[key]:03d}"
        cases.append(
            {
                "id": case_id,
                "language": language,
                "input": input_text,
                "expected_semantic_facts": facts,
                "expected_patterns": patterns,
                "negative_expected_patterns": negatives,
            }
        )

    return cases


def main() -> None:
    cases = build_cases()
    payload = {
        "version": 1,
        "description": (
            "NIROS psychedelic intake pattern matrix for multilingual self-reported "
            "intake testing. Signals only — not diagnosis, eligibility, or treatment claims."
        ),
        "cases": cases,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(payload, handle, sort_keys=False, allow_unicode=True, width=1000)
    print(f"Wrote {len(cases)} cases to {OUTPUT}")


if __name__ == "__main__":
    main()
