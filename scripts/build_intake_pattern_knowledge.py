#!/usr/bin/env python3
"""One-shot builder for Sprint 013 intake knowledge patterns."""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
PATTERNS_DIR = ROOT / "knowledge" / "patterns"
TEST_CASES_DIR = ROOT / "knowledge" / "test_cases"

DOMAINS = {
    "fear_safety_distress": "fear_safety_distress",
    "session_concerns": "session_concerns",
    "trauma_stress": "trauma_stress",
    "body_pain": "body_pain",
    "speech_communication": "speech_communication",
    "meaning_direction": "meaning_direction",
}

PATTERN_SPECS: list[dict] = [
    # Fear / Safety / Distress (4 new; 4 already exist separately)
    {
        "canonical_id": "panic_reactivity",
        "name": "Panic Reactivity",
        "domain": DOMAINS["fear_safety_distress"],
        "definition": "An observed signal that the person reports sudden panic or panic-like surges.",
        "behavioral_description": "The person may describe panic arriving quickly, body alarm spikes, or reported panic that feels hard to slow down.",
        "phrases": {
            "en": ["panic hits me out of nowhere", "I panic suddenly", "sudden panic takes over"],
            "uk": ["мене накриває паніка", "раптова паніка накриває мене", "у мене раптово починається паніка"],
            "ru": ["меня накрывает паника", "внезапная паника накрывает меня", "у меня внезапно начинается паника"],
            "es": ["el pánico me golpea de la nada", "entro en pánico de repente", "el pánico repentino me domina"],
        },
        "related": ["generalized_fear", "emotional_distress_signal"],
    },
    {
        "canonical_id": "fear_of_losing_control",
        "name": "Fear of Losing Control",
        "domain": DOMAINS["fear_safety_distress"],
        "definition": "An observed signal that the person reports fear about losing control of body, mind, or behavior.",
        "behavioral_description": "The person may describe fear of losing control, dread of uncontrollable reactions, or reported worry about not being able to manage themselves.",
        "phrases": {
            "en": ["I'm afraid of losing control", "I fear losing control of myself", "I'm scared I will lose control"],
            "uk": ["я боюся втратити контроль", "мені страшно втратити контроль", "я боюся втратити контроль над собою"],
            "ru": ["я боюсь потерять контроль", "мне страшно потерять контроль", "я боюсь потерять контроль над собой"],
            "es": ["tengo miedo de perder el control", "me da miedo perder el control de mí mismo", "temo perder el control"],
        },
        "related": ["panic_reactivity", "safety_concern_signal"],
    },
    {
        "canonical_id": "fear_of_death",
        "name": "Fear of Death",
        "domain": DOMAINS["fear_safety_distress"],
        "definition": "An observed signal that the person reports fear related to death or dying as a self-reported concern.",
        "behavioral_description": "The person may mention fear of dying, dread about death, or reported fear when thinking about mortality without clinical interpretation.",
        "phrases": {
            "en": ["I'm afraid of dying", "I fear death", "thoughts of death scare me"],
            "uk": ["я боюся смерті", "мені страшно про смерть", "думки про смерть мене лякають"],
            "ru": ["я боюсь смерти", "мне страшно про смерть", "мысли о смерти меня пугают"],
            "es": ["tengo miedo de morir", "me da miedo la muerte", "los pensamientos de muerte me asustan"],
        },
        "related": ["existential_fear", "safety_concern_signal"],
    },
    {
        "canonical_id": "fear_of_going_crazy",
        "name": "Fear of Going Crazy",
        "domain": DOMAINS["fear_safety_distress"],
        "definition": "An observed signal that the person reports fear of losing their mind or going crazy, stated in their own words.",
        "behavioral_description": "The person may say they fear going crazy, worry about losing their mind, or report fright about mental unraveling without diagnostic labeling.",
        "phrases": {
            "en": ["I'm afraid I'm going crazy", "I fear losing my mind", "I'm scared I'm losing my mind"],
            "uk": ["я боюся зійти з розуму", "мені страшно, що я сходжу з розуму", "я боюся втратити розум"],
            "ru": ["я боюсь сойти с ума", "мне страшно, что я схожу с ума", "я боюсь потерять рассудок"],
            "es": ["tengo miedo de volverme loco", "me da miedo perder la cabeza", "temo perder la razón"],
        },
        "related": ["fear_of_losing_control", "emotional_distress_signal"],
    },
    # Psychedelic Session Concerns
    {
        "canonical_id": "psychedelic_anxiety",
        "name": "Psychedelic Session Anxiety",
        "domain": DOMAINS["session_concerns"],
        "definition": "An observed signal that the person reports anxiety about a psychedelic or ceremonial session as a self-reported concern.",
        "behavioral_description": "The person may describe nervousness before a session, worry about the experience, or reported anxiety about what may happen in ceremony.",
        "phrases": {
            "en": ["I'm anxious about the ceremony", "I'm nervous about the psychedelic session", "I feel anxious before the session"],
            "uk": ["мене тривожить церемонія", "я хвилююся перед сесією", "мені тривожно перед досвідом"],
            "ru": ["меня тревожит церемония", "я волнуюсь перед сессией", "мне тревожно перед опытом"],
            "es": ["me siento ansioso por la ceremonia", "estoy nervioso por la sesión", "me da ansiedad antes de la sesión"],
        },
        "related": ["fear_of_bad_trip", "control_resistance"],
    },
    {
        "canonical_id": "surrender_difficulty",
        "name": "Surrender Difficulty",
        "domain": DOMAINS["session_concerns"],
        "definition": "An observed signal that the person reports difficulty letting go or surrendering during inner or ceremonial experiences.",
        "behavioral_description": "The person may describe trouble surrendering, needing control, or reported difficulty allowing the experience to unfold.",
        "phrases": {
            "en": ["I find it hard to surrender", "I struggle to let go during the experience", "I can't surrender easily"],
            "uk": ["мені важко відпустити контроль", "я не можу легко віддатися досвіду", "мені важко surrender під час сесії"],
            "ru": ["мне трудно отпустить контроль", "я не могу легко surrender во время сессии", "мне сложно отдаться опыту"],
            "es": ["me cuesta rendirme", "me cuesta soltar el control durante la experiencia", "no puedo surrender fácilmente"],
        },
        "related": ["control_resistance", "fear_of_losing_control"],
    },
    {
        "canonical_id": "control_resistance",
        "name": "Control Resistance",
        "domain": DOMAINS["session_concerns"],
        "definition": "An observed signal that the person reports resistance to losing control in session-related contexts.",
        "behavioral_description": "The person may describe needing to stay in control, resisting letting go, or reported control resistance during inner work.",
        "phrases": {
            "en": ["I resist letting go of control", "I need to stay in control", "I resist losing control in the session"],
            "uk": ["я опираюся втраті контролю", "мені потрібно тримати все під контролем", "я не хочу відпускати контроль"],
            "ru": ["я сопротивляюсь потере контроля", "мне нужно держать всё под контролем", "я не хочу отпускать контроль"],
            "es": ["resisto soltar el control", "necesito mantener el control", "me resisto a perder el control en la sesión"],
        },
        "related": ["surrender_difficulty", "fear_of_losing_control"],
    },
    {
        "canonical_id": "fear_of_bad_trip",
        "name": "Fear of Difficult Experience",
        "domain": DOMAINS["session_concerns"],
        "definition": "An observed signal that the person reports fear of a difficult or frightening session experience in their own words.",
        "behavioral_description": "The person may mention fear of a bad trip, dread of a frightening experience, or reported worry about the session going badly.",
        "phrases": {
            "en": ["I'm afraid of a bad trip", "I fear the experience will go badly", "I'm scared of a difficult trip"],
            "uk": ["я боюся поганого досвіду", "мені страшно, що досвід буде важким", "я боюся складного trip"],
            "ru": ["я боюсь плохого опыта", "мне страшно, что опыт будет трудным", "я боюсь bad trip"],
            "es": ["tengo miedo de un mal viaje", "temo que la experiencia salga mal", "me da miedo un trip difícil"],
        },
        "related": ["psychedelic_anxiety", "fear_of_body_sensations"],
    },
    {
        "canonical_id": "fear_of_body_sensations",
        "name": "Fear of Body Sensations",
        "domain": DOMAINS["session_concerns"],
        "definition": "An observed signal that the person reports fear of intense or unfamiliar body sensations.",
        "behavioral_description": "The person may describe fear of bodily feelings, worry about strong sensations, or reported fright when the body feels unusual.",
        "phrases": {
            "en": ["I'm afraid of strong body sensations", "intense body feelings scare me", "I'm scared of what I might feel in my body"],
            "uk": ["мені страшно від сильних відчуттів у тілі", "я боюся незвичних відчуттів у тілі", "інтенсивні body sensations мене лякають"],
            "ru": ["мне страшно от сильных телесных ощущений", "я боюсь необычных ощущений в теле", "интенсивные ощущения в теле меня пугают"],
            "es": ["me da miedo sentir sensaciones intensas en el cuerpo", "tengo miedo de sensaciones corporales fuertes", "me asustan las sensaciones físicas intensas"],
        },
        "related": ["somatic_anxiety", "fear_of_bad_trip"],
    },
    {
        "canonical_id": "trust_in_facilitator_difficulty",
        "name": "Facilitator Trust Difficulty",
        "domain": DOMAINS["session_concerns"],
        "definition": "An observed signal that the person reports difficulty trusting a facilitator, guide, or session holder.",
        "behavioral_description": "The person may describe trouble trusting the facilitator, worry about being held safely, or reported difficulty relying on session support.",
        "phrases": {
            "en": ["I find it hard to trust the facilitator", "I struggle to trust the guide", "I'm not sure I can trust the person holding the session"],
            "uk": ["мені важко довіряти фасилітатору", "я не впевнений, що можу довіритися провіднику", "важко довіритися тому, хто тримає сесію"],
            "ru": ["мне трудно доверять фасилитатору", "я не уверен, что могу довериться проводнику", "сложно довериться тому, кто держит сессию"],
            "es": ["me cuesta confiar en el facilitador", "me cuesta confiar en la guía", "no sé si puedo confiar en quien sostiene la sesión"],
        },
        "related": ["trust_difficulty", "safety_concern_signal"],
    },
    {
        "canonical_id": "spiritual_openness",
        "name": "Spiritual Openness",
        "domain": DOMAINS["session_concerns"],
        "definition": "An observed signal that the person reports openness to spiritual, inner, or meaning-oriented experience.",
        "behavioral_description": "The person may describe openness to inner experience, curiosity about spiritual themes, or reported willingness to explore meaning.",
        "phrases": {
            "en": ["I feel open to the spiritual side of this", "I'm open to inner experience", "I feel spiritually open to what may come"],
            "uk": ["я відкритий до духовного досвіду", "мені цікаво дослідити внутрішній досвід", "я відкритий до того, що може прийти"],
            "ru": ["я открыт к духовному опыту", "мне интересно исследовать внутренний опыт", "я открыт к тому, что может прийти"],
            "es": ["me siento abierto a la parte espiritual", "estoy abierto a la experiencia interior", "me siento espiritualmente abierto a lo que venga"],
        },
        "related": ["meaning_seeking", "mystical_expectation"],
    },
    {
        "canonical_id": "spiritual_resistance",
        "name": "Spiritual Resistance",
        "domain": DOMAINS["session_concerns"],
        "definition": "An observed signal that the person reports resistance to spiritual framing or inner/spiritual language.",
        "behavioral_description": "The person may describe discomfort with spiritual language, resistance to mystical framing, or reported preference to avoid spiritual themes.",
        "phrases": {
            "en": ["I'm resistant to spiritual language", "I feel uncomfortable with mystical framing", "I resist the spiritual side of this"],
            "uk": ["я опираюся духовному мовленню", "мені некомфортно з містичними формулюваннями", "я не хочу духовних рамок"],
            "ru": ["я сопротивляюсь духовному языку", "мне некомfortно с мистическими формулировками", "я не хочу духовных рамок"],
            "es": ["me resisto al lenguaje espiritual", "me incomoda el encuadre místico", "me resisto al lado espiritual de esto"],
        },
        "related": ["control_resistance", "spiritual_openness"],
    },
    {
        "canonical_id": "meaning_seeking",
        "name": "Meaning Seeking",
        "domain": DOMAINS["session_concerns"],
        "definition": "An observed signal that the person reports searching for meaning, purpose, or deeper understanding.",
        "behavioral_description": "The person may describe seeking meaning, wanting to understand themselves more deeply, or reported search for purpose.",
        "phrases": {
            "en": ["I'm searching for meaning", "I want to understand myself more deeply", "I'm looking for a deeper sense of purpose"],
            "uk": ["я шукаю sense of meaning", "хочу глибше зрозуміти себе", "шукаю глибший сенс"],
            "ru": ["я ищу смысл", "хочу глубже понять себя", "ищу более глубокий смысл"],
            "es": ["busco sentido", "quiero entenderme más profundamente", "busco un sentido más profundo"],
        },
        "related": ["search_for_self_understanding", "loss_of_meaning"],
    },
    {
        "canonical_id": "mystical_expectation",
        "name": "Mystical Expectation",
        "domain": DOMAINS["session_concerns"],
        "definition": "An observed signal that the person reports expectations about mystical, transcendent, or extraordinary experience.",
        "behavioral_description": "The person may describe expecting a mystical experience, hoping for transcendence, or reported anticipation of something extraordinary.",
        "phrases": {
            "en": ["I expect a mystical experience", "I hope for something transcendent", "I'm expecting an extraordinary experience"],
            "uk": ["я очікую містичного досвіду", "сподіваюся на transcendent experience", "очікую чогось надзвичайного"],
            "ru": ["я ожидаю мистического опыта", "надеюсь на transcendent experience", "ожидаю чего-то необычного"],
            "es": ["espero una experiencia mística", "espero algo trascendente", "anticipo una experiencia extraordinaria"],
        },
        "related": ["spiritual_openness", "meaning_seeking"],
    },
    {
        "canonical_id": "integration_need",
        "name": "Integration Need",
        "domain": DOMAINS["session_concerns"],
        "definition": "An observed signal that the person reports needing help integrating past or upcoming experience into daily life.",
        "behavioral_description": "The person may describe needing integration support, difficulty making sense after experience, or reported need to integrate insights.",
        "phrases": {
            "en": ["I need help integrating the experience", "integration feels important to me", "I need support making sense afterward"],
            "uk": ["мені потрібна integration після досвіду", "важливо інтегрувати досвід у життя", "потрібна підтримка, щоб осмислити досвід"],
            "ru": ["мне нужна integration после опыта", "важно интегрировать опыт в жизнь", "нужна поддержка, чтобы осмыслить опыт"],
            "es": ["necesito ayuda para integrar la experiencia", "la integración me parece importante", "necesito apoyo para darle sentido después"],
        },
        "related": ["meaning_seeking", "life_transition_distress"],
    },
    # Trauma / Stress
    {
        "canonical_id": "hypervigilance",
        "name": "Hypervigilance",
        "domain": DOMAINS["trauma_stress"],
        "definition": "An observed signal that the person reports staying on alert, scanning for danger, or difficulty relaxing vigilance.",
        "behavioral_description": "The person may describe always being on guard, scanning for threat, or reported difficulty feeling safe enough to relax.",
        "phrases": {
            "en": ["I'm always on alert", "I scan for danger constantly", "I can't relax my vigilance"],
            "uk": ["я постійно напоготові", "завжди scan for danger", "не можу розслабити пильність"],
            "ru": ["я постоянно настороже", "всё время scan for danger", "не могу расслабить бдительность"],
            "es": ["siempre estoy alerta", "escaneo el peligro constantemente", "no puedo relajar mi vigilancia"],
        },
        "related": ["startle_sensitivity", "safety_concern_signal"],
    },
    {
        "canonical_id": "emotional_numbing",
        "name": "Emotional Numbing",
        "domain": DOMAINS["trauma_stress"],
        "definition": "An observed signal that the person reports feeling emotionally numb, shut down, or disconnected from feeling.",
        "behavioral_description": "The person may describe numbness, feeling shut down, or reported difficulty accessing emotion.",
        "phrases": {
            "en": ["I feel emotionally numb", "I feel shut down inside", "my feelings feel distant or numb"],
            "uk": ["я емоційно онімінів", "всередині ніби все вимкнене", "почуття ніби distant or numb"],
            "ru": ["я эмоционально онемел", "внутри будто всё выключено", "чувства будто distant or numb"],
            "es": ["me siento emocionalmente entumecido", "me siento apagado por dentro", "mis sentimientos se sienten distantes o entumecidos"],
        },
        "related": ["dissociation_signal", "emotional_suppression"],
    },
    {
        "canonical_id": "intrusive_memories",
        "name": "Intrusive Memories",
        "domain": DOMAINS["trauma_stress"],
        "definition": "An observed signal that the person reports unwanted memories or images returning on their own.",
        "behavioral_description": "The person may describe memories intruding, unwanted images returning, or reported difficulty keeping past events out of mind.",
        "phrases": {
            "en": ["unwanted memories keep coming back", "intrusive memories return on their own", "images from the past intrude"],
            "uk": ["назад повертаються небажані спогади", "intrusive memories приходять самі", "минуле вторгається в думки"],
            "ru": ["возвращаются нежелательные воспоминания", "intrusive memories приходят сами", "прошлое вторгается в мысли"],
            "es": ["vuelven recuerdos no deseados", "los recuerdos intrusivos regresan solos", "el pasado se cuela en mis pensamientos"],
        },
        "related": ["avoidance_of_triggers", "rumination"],
    },
    {
        "canonical_id": "avoidance_of_triggers",
        "name": "Avoidance of Triggers",
        "domain": DOMAINS["trauma_stress"],
        "definition": "An observed signal that the person reports avoiding places, topics, or cues linked to distress.",
        "behavioral_description": "The person may describe avoiding triggers, steering away from reminders, or reported effort to stay away from distressing cues.",
        "phrases": {
            "en": ["I avoid triggers whenever I can", "I stay away from things that remind me", "I avoid situations that bring it back"],
            "uk": ["уникаю triggers, коли можу", "тримаюся подалі від нагадувань", "уникаю ситуацій, що повертають це"],
            "ru": ["избегаю triggers, когда могу", "держусь подальше от напоминаний", "избегаю ситуаций, которые это возвращают"],
            "es": ["evito los triggers cuando puedo", "me alejo de cosas que me lo recuerdan", "evito situaciones que lo traen de vuelta"],
        },
        "related": ["intrusive_memories", "emotional_avoidance"],
    },
    {
        "canonical_id": "startle_sensitivity",
        "name": "Startle Sensitivity",
        "domain": DOMAINS["trauma_stress"],
        "definition": "An observed signal that the person reports being easily startled or jumpy.",
        "behavioral_description": "The person may describe jumping at sudden sounds, being easily startled, or reported heightened startle response.",
        "phrases": {
            "en": ["I'm easily startled", "sudden sounds make me jump", "I startle very easily"],
            "uk": ["я легко startle", "різкі звуки мене лякають", "дуже легко злякатися"],
            "ru": ["я легко startle", "резкие звуки меня пугают", "очень легко испугаться"],
            "es": ["me asusto fácilmente", "los sonidos repentinos me hacen saltar", "soy muy susceptible al sobresalto"],
        },
        "related": ["hypervigilance", "anxiety_reactivity"],
    },
    {
        "canonical_id": "chronic_tension",
        "name": "Chronic Tension",
        "domain": DOMAINS["trauma_stress"],
        "definition": "An observed signal that the person reports ongoing bodily tension or tightness.",
        "behavioral_description": "The person may describe muscles staying tight, chronic bodily tension, or reported difficulty releasing physical holding.",
        "phrases": {
            "en": ["my body stays tense all the time", "I carry chronic tension", "I'm tight most of the day"],
            "uk": ["тіло постійно напружене", "живу з chronic tension", "більшість дня я напружений"],
            "ru": ["тело постоянно напряжено", "живу с chronic tension", "большую часть дня я напряжён"],
            "es": ["mi cuerpo permanece tenso todo el tiempo", "cargo tensión crónica", "estoy tenso la mayor parte del día"],
        },
        "related": ["somatic_anxiety", "chronic_pain_burden"],
    },
    {
        "canonical_id": "dissociation_signal",
        "name": "Dissociation Signal",
        "domain": DOMAINS["trauma_stress"],
        "definition": "An observed signal that the person reports feeling detached, unreal, or not fully present in their own words.",
        "behavioral_description": "The person may describe feeling unreal, spaced out, or reported detachment without diagnostic labeling.",
        "phrases": {
            "en": ["I feel detached from myself", "things feel unreal sometimes", "I feel spaced out"],
            "uk": ["я ніби detached from myself", "інколи все здається unreal", "ніби spaced out"],
            "ru": ["я будто detached from myself", "иногда всё кажется unreal", "будто spaced out"],
            "es": ["me siento desconectado de mí mismo", "a veces todo se siente irreal", "me siento desorientado"],
        },
        "related": ["emotional_numbing", "emotional_distress_signal"],
    },
    {
        "canonical_id": "shame_after_vulnerability",
        "name": "Shame After Vulnerability",
        "domain": DOMAINS["trauma_stress"],
        "definition": "An observed signal that the person reports shame after opening up or showing vulnerability.",
        "behavioral_description": "The person may describe feeling ashamed after sharing, regret after being vulnerable, or reported shame once openness passes.",
        "phrases": {
            "en": ["I feel ashamed after opening up", "shame hits me after I show vulnerability", "I regret being vulnerable afterward"],
            "uk": ["мені соромно після того, як відкрився", "сором приходить після vulnerability", " шкода, що був відкритим"],
            "ru": ["мне стыдно после того, как открылся", "стыд приходит после vulnerability", "жалею, что был уязвим"],
            "es": ["me da vergüenza después de abrirme", "la vergüenza llega después de mostrar vulnerabilidad", "me arrepiento de haberme mostrado vulnerable"],
        },
        "related": ["shame_sensitivity", "emotional_distress_signal"],
    },
    # Body / Pain
    {
        "canonical_id": "chronic_pain_burden",
        "name": "Chronic Pain Burden",
        "domain": DOMAINS["body_pain"],
        "definition": "An observed signal that the person reports ongoing pain burden affecting daily life.",
        "behavioral_description": "The person may describe constant pain, pain wearing them down, or reported pain burden without medical classification.",
        "phrases": {
            "en": ["my body hurts all the time", "chronic pain wears me down", "I'm living with constant pain"],
            "uk": ["моє тіло постійно болить", "хронічний біль виснажує мене", "живу з постійним болем"],
            "ru": ["моё тело постоянно болит", "хроническая боль изматывает меня", "живу с постоянной болью"],
            "es": ["mi cuerpo duele todo el tiempo", "el dolor crónico me agota", "vivo con dolor constante"],
        },
        "related": ["fatigue_burden", "pain_fear_cycle"],
    },
    {
        "canonical_id": "fatigue_burden",
        "name": "Fatigue Burden",
        "domain": DOMAINS["body_pain"],
        "definition": "An observed signal that the person reports persistent fatigue or exhaustion burden.",
        "behavioral_description": "The person may describe being exhausted most of the time, fatigue limiting activity, or reported depletion.",
        "phrases": {
            "en": ["I'm exhausted all the time", "fatigue limits what I can do", "I feel depleted most days"],
            "uk": ["я постійно виснажений", "втома обмежує, що я можу робити", "більшість днів відчуваю depletion"],
            "ru": ["я постоянно exhausted", "усталость ограничивает, что я могу делать", "большинство дней чувствую depletion"],
            "es": ["estoy agotado todo el tiempo", "la fatiga limita lo que puedo hacer", "me siento agotado la mayoría de los días"],
        },
        "related": ["chronic_pain_burden", "sleep_disruption"],
    },
    {
        "canonical_id": "body_sensitivity",
        "name": "Body Sensitivity",
        "domain": DOMAINS["body_pain"],
        "definition": "An observed signal that the person reports heightened sensitivity to touch, pressure, or bodily sensation.",
        "behavioral_description": "The person may describe the body feeling overly sensitive, touch hurting more than expected, or reported heightened bodily sensitivity.",
        "phrases": {
            "en": ["my body feels overly sensitive", "touch hurts more than it should", "I'm very sensitive to body sensations"],
            "uk": ["тіло надто sensitive", "дотик болить сильніше, ніж мав би", "дуже чутливий до body sensations"],
            "ru": ["тело слишком sensitive", "прикосновение болит сильнее, чем должно", "очень чувствителен к body sensations"],
            "es": ["mi cuerpo se siente demasiado sensible", "el tacto duele más de lo que debería", "soy muy sensible a las sensaciones corporales"],
        },
        "related": ["somatic_anxiety", "symptom_unpredictability"],
    },
    {
        "canonical_id": "pain_fear_cycle",
        "name": "Pain Fear Cycle",
        "domain": DOMAINS["body_pain"],
        "definition": "An observed signal that the person reports fear increasing because of pain or pain increasing because of fear.",
        "behavioral_description": "The person may describe pain and fear feeding each other, dread of pain flares, or reported cycle between pain and fear.",
        "phrases": {
            "en": ["pain and fear feed each other", "I'm afraid the pain will get worse", "fear makes the pain feel worse"],
            "uk": ["біль і страх підживлюють one another", "боюся, що біль посилиться", "страх робить біль гіршим"],
            "ru": ["боль и страх подпитывают other", "боюсь, что боль усилится", "страх делает боль хуже"],
            "es": ["el dolor y el miedo se alimentan mutuamente", "tengo miedo de que el dolor empeore", "el miedo empeora el dolor"],
        },
        "related": ["chronic_pain_burden", "somatic_anxiety"],
    },
    {
        "canonical_id": "symptom_unpredictability",
        "name": "Symptom Unpredictability",
        "domain": DOMAINS["body_pain"],
        "definition": "An observed signal that the person reports unpredictable symptoms or not knowing how the body will feel.",
        "behavioral_description": "The person may describe symptoms changing unpredictably, not knowing what the body will do, or reported uncertainty about symptom flares.",
        "phrases": {
            "en": ["my symptoms are unpredictable", "I never know how my body will feel", "symptoms flare without warning"],
            "uk": ["symptoms unpredictable", "ніколи не знаю, як почуватиметься тіло", "симптоми flare without warning"],
            "ru": ["symptoms unpredictable", "никогда не знаю, как будет feel тело", "симптомы flare without warning"],
            "es": ["mis síntomas son impredecibles", "nunca sé cómo se sentirá mi cuerpo", "los síntomas aparecen sin aviso"],
        },
        "related": ["activity_avoidance_due_to_pain", "body_trust_difficulty"],
    },
    {
        "canonical_id": "sleep_disruption",
        "name": "Sleep Disruption",
        "domain": DOMAINS["body_pain"],
        "definition": "An observed signal that the person reports disrupted sleep affecting how they feel.",
        "behavioral_description": "The person may describe trouble sleeping, broken sleep, or reported sleep disruption without medical labeling.",
        "phrases": {
            "en": ["my sleep is disrupted", "I can't sleep properly", "broken sleep wears me out"],
            "uk": ["сон порушений", "не можу нормально спати", "перерваний сон виснажує"],
            "ru": ["сон нарушен", "не могу нормально спать", "прерывистый сон изматывает"],
            "es": ["mi sueño está interrumpido", "no puedo dormir bien", "el sueño roto me agota"],
        },
        "related": ["nightmare_disturbance", "fatigue_burden"],
    },
    {
        "canonical_id": "somatic_anxiety",
        "name": "Somatic Anxiety",
        "domain": DOMAINS["body_pain"],
        "definition": "An observed signal that the person reports anxiety showing up strongly in the body.",
        "behavioral_description": "The person may describe anxiety in the body, physical alarm without clear cause, or reported bodily anxiety.",
        "phrases": {
            "en": ["anxiety lives in my body", "my body holds a lot of anxiety", "I feel anxious physically"],
            "uk": ["тривога живе в моєму тілі", "тіло тримає багато anxiety", "фізично відчуваю тривогу"],
            "ru": ["тревога живёт в моём теле", "тело держит много anxiety", "физически чувствую тревогу"],
            "es": ["la ansiedad vive en mi cuerpo", "mi cuerpo guarda mucha ansiedad", "siento ansiedad físicamente"],
        },
        "related": ["anxiety_reactivity", "body_sensitivity"],
    },
    {
        "canonical_id": "body_trust_difficulty",
        "name": "Body Trust Difficulty",
        "domain": DOMAINS["body_pain"],
        "definition": "An observed signal that the person reports difficulty trusting or feeling safe in their body.",
        "behavioral_description": "The person may describe not trusting the body, feeling betrayed by bodily signals, or reported difficulty relying on physical cues.",
        "phrases": {
            "en": ["I don't trust my body", "my body feels unreliable", "I can't feel safe in my body"],
            "uk": ["я не довіряю своєму тілу", "тіло здається unreliable", "не можу почуватися safe in my body"],
            "ru": ["я не доверяю своему телу", "тело кажется unreliable", "не могу чувствовать себя safe in my body"],
            "es": ["no confío en mi cuerpo", "mi cuerpo se siente poco confiable", "no puedo sentirme seguro en mi cuerpo"],
        },
        "related": ["body_sensitivity", "safety_concern_signal"],
    },
    {
        "canonical_id": "activity_avoidance_due_to_pain",
        "name": "Activity Avoidance Due to Pain",
        "domain": DOMAINS["body_pain"],
        "definition": "An observed signal that the person reports avoiding activity because of pain or symptom flares.",
        "behavioral_description": "The person may describe skipping activity due to pain, fear of making pain worse, or reported avoidance of movement.",
        "phrases": {
            "en": ["I avoid activity because of pain", "pain keeps me from doing things", "I skip activities when pain flares"],
            "uk": ["уникаю activity because of pain", "біль не дає робити речі", "пропускаю справи, коли pain flares"],
            "ru": ["избегаю activity because of pain", "боль не даёт делать дела", "пропускаю дела, когда pain flares"],
            "es": ["evito actividad por el dolor", "el dolor me impide hacer cosas", "dejo actividades cuando el dolor empeora"],
        },
        "related": ["chronic_pain_burden", "pain_fear_cycle"],
    },
    {
        "canonical_id": "frustration_with_medical_system",
        "name": "Frustration With Medical System",
        "domain": DOMAINS["body_pain"],
        "definition": "An observed signal that the person reports frustration with medical care or not feeling understood by providers.",
        "behavioral_description": "The person may describe feeling dismissed by doctors, frustration with medical care, or reported lack of being heard about symptoms.",
        "phrases": {
            "en": ["doctors don't understand my pain", "I'm frustrated with the medical system", "I feel dismissed by medical providers"],
            "uk": ["лікарі не розуміють мій біль", "frustrated with medical system", "відчуваю, що мене dismissed by providers"],
            "ru": ["врачи не понимают мою боль", "frustrated with medical system", "чувствую, что меня dismissed by providers"],
            "es": ["los médicos no entienden mi dolor", "estoy frustrado con el sistema médico", "me siento ignorado por los médicos"],
        },
        "related": ["chronic_pain_burden", "body_trust_difficulty"],
    },
    # Speech
    {
        "canonical_id": "speech_anxiety",
        "name": "Speech Anxiety",
        "domain": DOMAINS["speech_communication"],
        "definition": "An observed signal that the person reports anxiety specifically related to speaking.",
        "behavioral_description": "The person may describe anxiety before speaking, nervousness about talking, or reported speech-related tension.",
        "phrases": {
            "en": ["I get anxious when I have to speak", "speaking makes me nervous", "I feel speech anxiety"],
            "uk": ["мені тривожно, коли треба говорити", "говоріння викликає nervousness", "відчуваю speech anxiety"],
            "ru": ["мне тревожно, когда нужно говорить", "говорение вызывает nervousness", "чувствую speech anxiety"],
            "es": ["me pongo ansioso cuando tengo que hablar", "hablar me pone nervioso", "siento ansiedad al hablar"],
        },
        "related": ["fear_of_speaking", "anticipation_anxiety"],
    },
    {
        "canonical_id": "fear_of_speaking",
        "name": "Fear of Speaking",
        "domain": DOMAINS["speech_communication"],
        "definition": "An observed signal that the person reports fear of speaking in front of others or being heard while speaking.",
        "behavioral_description": "The person may describe fear of speaking up, dread of talking in groups, or reported fright about being heard.",
        "phrases": {
            "en": ["I'm afraid to speak in front of people", "I fear speaking up", "I'm scared to talk when others listen"],
            "uk": ["я боюся говорити перед людьми", "страшно speak up", "боюся говорити, коли слухають інші"],
            "ru": ["я боюсь говорить перед людьми", "страшно speak up", "боюсь говорить, когда слушают другие"],
            "es": ["tengo miedo de hablar delante de la gente", "me da miedo hablar", "me da miedo hablar cuando otros escuchan"],
        },
        "related": ["speech_anxiety", "social_visibility_fear"],
    },
    {
        "canonical_id": "communication_avoidance",
        "name": "Communication Avoidance",
        "domain": DOMAINS["speech_communication"],
        "definition": "An observed signal that the person reports avoiding conversations or communication situations.",
        "behavioral_description": "The person may describe avoiding talking, staying quiet to avoid speech, or reported communication avoidance.",
        "phrases": {
            "en": ["I avoid conversations when I can", "I stay quiet to avoid speaking", "I avoid communication situations"],
            "uk": ["уникаю розмов, коли можу", "мовчу, щоб avoid speaking", "уникаю communication situations"],
            "ru": ["избегаю разговоров, когда могу", "молчу, чтобы avoid speaking", "избегаю communication situations"],
            "es": ["evito conversaciones cuando puedo", "me quedo callado para evitar hablar", "evito situaciones de comunicación"],
        },
        "related": ["fear_of_speaking", "conflict_avoidance"],
    },
    {
        "canonical_id": "shame_about_speech",
        "name": "Shame About Speech",
        "domain": DOMAINS["speech_communication"],
        "definition": "An observed signal that the person reports shame related to how they speak or communicate.",
        "behavioral_description": "The person may describe shame about stuttering, embarrassment about speech, or reported shame when talking.",
        "phrases": {
            "en": ["I'm ashamed of how I speak", "I feel shame about my speech", "I stutter and feel ashamed"],
            "uk": ["мені соромно за те, як я говорю", "сором through speech", "заікаюся і мені соромно"],
            "ru": ["мне стыдно за то, как я говорю", "стыд through speech", "заикаюсь и мне стыдно"],
            "es": ["me da vergüenza cómo hablo", "siento vergüenza de mi forma de hablar", "tartamudeo y me da vergüenza"],
        },
        "related": ["shame_sensitivity", "speech_anxiety"],
    },
    {
        "canonical_id": "anticipation_anxiety",
        "name": "Anticipation Anxiety",
        "domain": DOMAINS["speech_communication"],
        "definition": "An observed signal that the person reports anxiety building before speaking or being visible.",
        "behavioral_description": "The person may describe dread before talking, anxiety rising in anticipation, or reported pre-speech tension.",
        "phrases": {
            "en": ["I dread speaking before it even starts", "anticipation anxiety builds before I talk", "I worry long before I have to speak"],
            "uk": ["anticipation anxiety перед тим, як говорити", "тривога наростає до розмови", "хвилююся задовго до того, як треба говорити"],
            "ru": ["anticipation anxiety перед тем, как говорить", "тревога нарастает до разговора", "волнуюсь задолго до того, как нужно говорить"],
            "es": ["anticipo ansiedad antes de hablar", "la ansiedad crece antes de hablar", "me preocupo mucho antes de tener que hablar"],
        },
        "related": ["speech_anxiety", "social_visibility_fear"],
    },
    {
        "canonical_id": "social_visibility_fear",
        "name": "Social Visibility Fear",
        "domain": DOMAINS["speech_communication"],
        "definition": "An observed signal that the person reports fear of being seen, heard, or noticed by others.",
        "behavioral_description": "The person may describe fear of visibility, dread of being noticed, or reported discomfort being seen while speaking.",
        "phrases": {
            "en": ["I'm afraid of being noticed when I speak", "I fear being visible to others", "I hate being seen while talking"],
            "uk": ["боюся, що помітять, коли говорю", "страшно being visible to others", "не люблю, коли мене seen while talking"],
            "ru": ["боюсь, что заметят, когда говорю", "страшно being visible to others", "не люблю, когда меня seen while talking"],
            "es": ["tengo miedo de que me noten cuando hablo", "temo ser visible para otros", "odio que me vean mientras hablo"],
        },
        "related": ["fear_of_speaking", "shame_about_speech"],
    },
    {
        "canonical_id": "loss_of_control_in_speech",
        "name": "Loss of Control in Speech",
        "domain": DOMAINS["speech_communication"],
        "definition": "An observed signal that the person reports fear or difficulty controlling speech flow.",
        "behavioral_description": "The person may describe words getting stuck, losing control while speaking, or reported difficulty controlling speech.",
        "phrases": {
            "en": ["I lose control when I try to speak", "words get stuck and I panic", "I can't control my speech flow"],
            "uk": ["втрачаю control when I try to speak", "слова застрягають і я panic", "не можу control my speech flow"],
            "ru": ["теряю control when I try to speak", "слова застревают и я panic", "не могу control my speech flow"],
            "es": ["pierdo el control cuando intento hablar", "las palabras se atascan y entro en pánico", "no puedo controlar mi flujo al hablar"],
        },
        "related": ["fear_of_losing_control", "speech_anxiety"],
    },
    {
        "canonical_id": "self_expression_block",
        "name": "Self-Expression Block",
        "domain": DOMAINS["speech_communication"],
        "definition": "An observed signal that the person reports difficulty expressing themselves openly.",
        "behavioral_description": "The person may describe blocked self-expression, trouble saying what they mean, or reported difficulty speaking authentically.",
        "phrases": {
            "en": ["I block myself from expressing what I feel", "I can't express myself openly", "my words won't come out the way I mean"],
            "uk": ["блокую self-expression", "не можу openly express myself", "слова не виходять так, як хочу"],
            "ru": ["блокирую self-expression", "не могу openly express myself", "слова не выходят так, как хочу"],
            "es": ["me bloqueo al expresar lo que siento", "no puedo expresarme abiertamente", "mis palabras no salen como quiero"],
        },
        "related": ["communication_avoidance", "emotional_suppression"],
    },
    # Meaning / Direction
    {
        "canonical_id": "hopelessness_signal",
        "name": "Hopelessness Signal",
        "domain": DOMAINS["meaning_direction"],
        "definition": "An observed signal that the person reports hopelessness or little sense that things can improve.",
        "behavioral_description": "The person may describe feeling hopeless, seeing little way forward, or reported loss of hope without diagnostic labeling.",
        "phrases": {
            "en": ["I feel hopeless", "I don't see a way forward", "hope feels far away"],
            "uk": ["я відчуваю hopeless", "не бачу way forward", "надія здається далекою"],
            "ru": ["я чувствую hopeless", "не вижу way forward", "надежда кажется далёкой"],
            "es": ["me siento sin esperanza", "no veo un camino adelante", "la esperanza se siente lejana"],
        },
        "related": ["loss_of_meaning", "existential_fear"],
    },
    {
        "canonical_id": "loss_of_meaning",
        "name": "Loss of Meaning",
        "domain": DOMAINS["meaning_direction"],
        "definition": "An observed signal that the person reports life feeling meaningless or empty of purpose.",
        "behavioral_description": "The person may describe loss of meaning, emptiness about purpose, or reported difficulty finding significance.",
        "phrases": {
            "en": ["life feels meaningless", "I've lost a sense of meaning", "nothing feels meaningful anymore"],
            "uk": ["життя здається meaningless", "втратив sense of meaning", "нічого не здається meaningful anymore"],
            "ru": ["жизнь кажется meaningless", "потерял sense of meaning", "ничего не кажется meaningful anymore"],
            "es": ["la vida se siente sin sentido", "he perdido el sentido de la vida", "nada se siente con significado"],
        },
        "related": ["hopelessness_signal", "meaning_seeking"],
    },
    {
        "canonical_id": "identity_confusion",
        "name": "Identity Confusion",
        "domain": DOMAINS["meaning_direction"],
        "definition": "An observed signal that the person reports confusion about who they are or where they belong.",
        "behavioral_description": "The person may describe not knowing who they are, identity confusion, or reported uncertainty about self-definition.",
        "phrases": {
            "en": ["I don't know who I am anymore", "I feel confused about my identity", "identity feels unclear"],
            "uk": ["не знаю, хто я зараз", "identity feels confused", "identity feels unclear"],
            "ru": ["не знаю, кто я сейчас", "identity feels confused", "identity feels unclear"],
            "es": ["no sé quién soy ahora", "me siento confundido sobre mi identidad", "mi identidad se siente confusa"],
        },
        "related": ["identity_uncertainty", "search_for_self_understanding"],
    },
    {
        "canonical_id": "life_transition_distress",
        "name": "Life Transition Distress",
        "domain": DOMAINS["meaning_direction"],
        "definition": "An observed signal that the person reports distress linked to a major life change or transition.",
        "behavioral_description": "The person may describe struggling with change, distress during transition, or reported difficulty adapting to a new life phase.",
        "phrases": {
            "en": ["this life transition is overwhelming", "I'm struggling with a big change", "change is distressing me a lot"],
            "uk": ["life transition overwhelming", "важко переживаю big change", "change distressing me a lot"],
            "ru": ["life transition overwhelming", "тяжело переживаю big change", "change distressing me a lot"],
            "es": ["esta transición de vida me abruma", "me cuesta una gran cambio", "el cambio me angustia mucho"],
        },
        "related": ["inner_conflict", "desire_for_change"],
    },
    {
        "canonical_id": "inner_conflict",
        "name": "Inner Conflict",
        "domain": DOMAINS["meaning_direction"],
        "definition": "An observed signal that the person reports being torn between different inner directions or values.",
        "behavioral_description": "The person may describe inner conflict, feeling pulled two ways, or reported struggle between competing wants.",
        "phrases": {
            "en": ["I feel torn inside", "I'm in conflict with myself", "part of me wants one thing and part another"],
            "uk": ["всередині torn", "конфліктую with myself", "one part wants one thing and part another"],
            "ru": ["внутри torn", "конфликтую with myself", "one part wants one thing and part another"],
            "es": ["me siento dividido por dentro", "estoy en conflicto conmigo mismo", "una parte quiere una cosa y otra otra"],
        },
        "related": ["identity_confusion", "life_transition_distress"],
    },
    {
        "canonical_id": "desire_for_change",
        "name": "Desire for Change",
        "domain": DOMAINS["meaning_direction"],
        "definition": "An observed signal that the person reports wanting meaningful change in life or self.",
        "behavioral_description": "The person may describe wanting change, readiness to shift something, or reported desire for a different path.",
        "phrases": {
            "en": ["I want meaningful change", "I need something in my life to change", "I'm ready for a different path"],
            "uk": ["хочу meaningful change", "потрібно, щоб щось change in my life", "ready for a different path"],
            "ru": ["хочу meaningful change", "нужно, чтобы что-то change in my life", "ready for a different path"],
            "es": ["quiero un cambio significativo", "necesito que algo cambie en mi vida", "estoy listo para un camino diferente"],
        },
        "related": ["search_for_self_understanding", "meaning_seeking"],
    },
    {
        "canonical_id": "search_for_self_understanding",
        "name": "Search for Self-Understanding",
        "domain": DOMAINS["meaning_direction"],
        "definition": "An observed signal that the person reports actively searching to understand themselves better.",
        "behavioral_description": "The person may describe wanting self-understanding, exploring inner patterns, or reported search for clarity about self.",
        "phrases": {
            "en": ["I'm trying to understand myself better", "I want more self-understanding", "I'm searching to know myself more clearly"],
            "uk": ["намагаюся understand myself better", "хочу більше self-understanding", "searching to know myself more clearly"],
            "ru": ["пытаюсь understand myself better", "хочу больше self-understanding", "searching to know myself more clearly"],
            "es": ["intento entenderme mejor", "quiero más autocomprensión", "busco conocerme con más claridad"],
        },
        "related": ["meaning_seeking", "identity_confusion"],
    },
]

INTEGRATED_SCENARIOS = {
    "024_fear_safety_distress_integrated.md": {
        "domain": DOMAINS["fear_safety_distress"],
        "lines": [
            "I'm afraid to live.",
            "panic hits me out of nowhere",
            "I'm afraid of losing control",
            "I'm afraid of dying",
            "I'm afraid I'm going crazy",
        ],
        "patterns": [
            "existential_fear",
            "panic_reactivity",
            "fear_of_losing_control",
            "fear_of_death",
            "fear_of_going_crazy",
            "safety_concern_signal",
        ],
    },
    "025_session_concerns_integrated.md": {
        "domain": DOMAINS["session_concerns"],
        "lines": [
            "I'm anxious about the ceremony",
            "I'm afraid of a bad trip",
            "I find it hard to surrender",
            "I'm searching for meaning",
            "I need help integrating the experience",
        ],
        "patterns": [
            "psychedelic_anxiety",
            "fear_of_bad_trip",
            "surrender_difficulty",
            "meaning_seeking",
            "integration_need",
        ],
    },
    "026_trauma_stress_integrated.md": {
        "domain": DOMAINS["trauma_stress"],
        "lines": [
            "I'm always on alert",
            "unwanted memories keep coming back",
            "I avoid triggers whenever I can",
            "I feel emotionally numb",
            "I feel detached from myself",
        ],
        "patterns": [
            "hypervigilance",
            "intrusive_memories",
            "avoidance_of_triggers",
            "emotional_numbing",
            "dissociation_signal",
        ],
    },
    "027_body_pain_integrated.md": {
        "domain": DOMAINS["body_pain"],
        "lines": [
            "my body hurts all the time",
            "I'm exhausted all the time",
            "my symptoms are unpredictable",
            "I don't trust my body",
            "doctors don't understand my pain",
        ],
        "patterns": [
            "chronic_pain_burden",
            "fatigue_burden",
            "symptom_unpredictability",
            "body_trust_difficulty",
            "frustration_with_medical_system",
        ],
    },
    "028_speech_communication_integrated.md": {
        "domain": DOMAINS["speech_communication"],
        "lines": [
            "I get anxious when I have to speak",
            "I'm afraid to speak in front of people",
            "I stutter and feel ashamed",
            "I dread speaking before it even starts",
            "I block myself from expressing what I feel",
        ],
        "patterns": [
            "speech_anxiety",
            "fear_of_speaking",
            "shame_about_speech",
            "anticipation_anxiety",
            "self_expression_block",
        ],
    },
    "029_meaning_direction_integrated.md": {
        "domain": DOMAINS["meaning_direction"],
        "lines": [
            "I feel hopeless",
            "life feels meaningless",
            "I don't know who I am anymore",
            "I feel torn inside",
            "I'm trying to understand myself better",
        ],
        "patterns": [
            "hopelessness_signal",
            "loss_of_meaning",
            "identity_confusion",
            "inner_conflict",
            "search_for_self_understanding",
        ],
    },
}


def build_pattern_yaml(spec: dict) -> dict:
    related = spec["related"]
    relationships = []
    for index, target in enumerate(related[:3]):
        relationships.append(
            {
                "target_pattern": target,
                "relation_type": "often_coexists_with",
                "weight": round(0.80 - index * 0.05, 2),
            }
        )
    return {
        "canonical_id": spec["canonical_id"],
        "name": spec["name"],
        "domain": spec["domain"],
        "definition": spec["definition"],
        "behavioral_description": spec["behavioral_description"],
        "positive_evidence": [
            "Reported language matching this observed signal.",
            "Repeated self-report consistent with this pattern.",
        ],
        "negative_evidence": [
            "Clear contradictory self-report.",
            "Neutral statement without this signal.",
        ],
        "typical_phrases": spec["phrases"],
        "follow_up_questions": {
            "en": [
                "Can you say more about that in your own words?",
                "When does this show up most strongly?",
                "What, if anything, helps even a little?",
            ],
            "uk": [
                "Можете сказати більше своїми словами?",
                "Коли це проявляється найсильніше?",
                "Що, якщо взагалі щось, трохи допомагає?",
            ],
            "ru": [
                "Можете сказать больше своими словами?",
                "Когда это проявляется сильнее всего?",
                "Что, если вообще что-то, немного помогает?",
            ],
            "es": [
                "¿Puede decir más con sus propias palabras?",
                "¿Cuándo aparece con más fuerza?",
                "¿Qué, si algo, ayuda aunque sea un poco?",
            ],
        },
        "related_patterns": related,
        "relationships": relationships,
        "confidence_rules": {
            "repeated_evidence": 0.15,
            "contradiction_present": -0.25,
            "strong_emotional_intensity": 0.20,
            "grounding_present": -0.10,
        },
        "interview_priority": 8,
        "therapeutic_relevance": (
            "Important for intake understanding of self-reported signals without diagnosis, "
            "eligibility decisions, or treatment recommendations."
        ),
    }


def write_human_case(path: Path, spec: dict) -> None:
    primary = spec["phrases"]["en"][0]
    extra = spec["phrases"]["en"][1:3]
    lines = [primary, *extra]
    content = "\n".join(
        [
            "# Scenario",
            *lines,
            "# Expected Patterns",
            f"- {spec['canonical_id']}",
            "# Expected Follow-up Domains",
            f"- {spec['domain']}",
            "- intake",
        ]
    )
    path.write_text(content + "\n", encoding="utf-8")


def write_integrated_case(path: Path, scenario: dict) -> None:
    content = "\n".join(
        [
            "# Scenario",
            *scenario["lines"],
            "# Expected Patterns",
            *[f"- {pattern_id}" for pattern_id in scenario["patterns"]],
            "# Expected Follow-up Domains",
            f"- {scenario['domain']}",
            "- intake",
        ]
    )
    path.write_text(content + "\n", encoding="utf-8")


def main() -> None:
    start_index = 30
    for offset, spec in enumerate(PATTERN_SPECS):
        pattern_path = PATTERNS_DIR / f"{spec['canonical_id']}.yaml"
        pattern_path.write_text(
            yaml.safe_dump(build_pattern_yaml(spec), sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        case_number = start_index + offset
        case_path = TEST_CASES_DIR / f"{case_number:03d}_{spec['canonical_id']}.md"
        write_human_case(case_path, spec)

    for filename, scenario in INTEGRATED_SCENARIOS.items():
        write_integrated_case(TEST_CASES_DIR / filename, scenario)

    print(f"Wrote {len(PATTERN_SPECS)} patterns and {len(INTEGRATED_SCENARIOS)} integrated cases.")


if __name__ == "__main__":
    main()
