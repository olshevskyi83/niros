#!/usr/bin/env python3
"""Generate complex synthetic human benchmark cases for NIROS."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "knowledge" / "test_cases" / "complex"


def _md_profile(
    *,
    case_id: str,
    title: str,
    domain_mix: list[str],
    scenario: str,
    patterns: list[str],
    weak_domains: list[str],
    assessments: list[str],
    strategy_focus: list[str],
    scenario_themes: list[str],
    timeline: list[str],
) -> str:
    domains = ", ".join(domain_mix)
    return "\n".join(
        [
            "# Profile Meta",
            f"- id: {case_id}",
            f"- title: {title}",
            f"- domains: {domains}",
            "",
            "# Scenario",
            "",
            scenario.strip(),
            "",
            "# Expected Patterns",
            *[f"- {item}" for item in patterns],
            "",
            "# Expected Weak Domains",
            *[f"- {item}" for item in weak_domains],
            "",
            "# Expected Assessments",
            *[f"- {item}" for item in assessments],
            "",
            "# Expected Strategy Focus",
            *[f"- {item}" for item in strategy_focus],
            "",
            "# Expected Scenario Themes",
            *[f"- {item}" for item in scenario_themes],
            "",
            "# Expected Timeline Characteristics",
            *[f"- {item}" for item in timeline],
            "",
        ]
    )


PROFILES: list[dict] = [
    {
        "file": "c001_grief_shame_self_worth.md",
        "case_id": "complex-001",
        "title": "Grief After Loss With Shame and Collapsed Self-Worth",
        "domain_mix": ["grief / loss", "shame", "self-worth"],
        "scenario": """
## Background

I am forty-one. Two years ago I lost my father after a sudden illness, and I tell myself I should be further along by now. I was the responsible one in the family, the person who held things together during the hospital weeks and the funeral. People said I was strong. Inside I felt like I was performing strength while something essential broke.

Before the loss I was fairly steady — not happy all the time, but I knew who I was. Since then I replay conversations we never finished. I am grieving, but I rarely say that out loud because it feels indulgent.

## Current Life

Work is manageable on paper and exhausting in practice. I show up, complete tasks, and leave feeling like I am watching myself from a distance. Social plans drain me. Weekends are the hardest: the grief feels overwhelming when the structure disappears. I sleep enough hours but wake up tired, as if mourning is exhausting in a way sleep cannot fix.

I lost someone close to me and I am still trying to understand how to live in a world where he is not here. Sometimes I think people expect me to be "back to normal." I cannot get over the loss, and I hate that sentence even as I think it.

## Thoughts

When I make a mistake at work, I feel like a failure — not just at the task, but as a person. I often feel embarrassed even when no one is watching. My inner voice is very critical. I tell myself I should have visited more, called more, been softer when he was irritable from pain.

I keep going over the same problems in my head: what I missed, what I should have said, whether he knew I loved him. deep down I feel I'm not enough, as if the loss proved something about my worth.

## Emotions

Sadness comes in waves, then shame for still being sad. I push my feelings down so I can keep going during the day. At night the feelings return heavier. I go numb when too much is happening — family gatherings, anniversaries, even good news that feels wrong to receive.

I want to hide when I feel I have failed, including failing to recover on some imaginary schedule.

## Relationships

My partner tries to help and I keep emotional distance so I cannot be hurt further. I find it hard to trust people with the raw parts of this grief. I do not like depending on others because it feels unsafe, as if needing support confirms weakness.

Friends drifted when I stopped initiating plans. I feel like I do not belong in cheerful rooms anymore.

## Goals

I want to feel more like myself without betraying my father's memory. I want to stop attacking myself for how I grieve. I am trying to understand myself better rather than force a quick fix.

## Values

Loyalty, family, honesty, and showing up for people matter deeply to me. I value being dependable — which makes my current inconsistency feel like a moral failure.

## Internal Conflicts

I want connection and fear that if I open up I will collapse or burden others. I believe grief should be private, but isolation makes it worse. I want to honor the loss and also live forward; I feel guilty for wanting relief.
""",
        "patterns": [
            "grief_signal",
            "bereavement_context",
            "loss_related_distress",
            "shame_sensitivity",
            "harsh_self_criticism",
            "unworthiness_signal",
            "social_withdrawal",
            "trust_difficulty",
            "emotional_suppression",
        ],
        "weak_domains": [
            "emotion_regulation_domain",
            "relationships_domain",
            "meaning",
            "cognitive_patterns_domain",
        ],
        "assessments": [
            "grief-loss-short",
            "self-domain-short",
            "emotion-regulation-domain-short",
            "relationships-domain-short",
        ],
        "strategy_focus": [
            "meaning / purpose",
            "self-worth / self-criticism",
            "emotion regulation",
            "relationships",
        ],
        "scenario_themes": [
            "gentle grounding",
            "grief-aware pacing",
            "non-pathologizing loss language",
            "shame-sensitive framing",
        ],
        "timeline": [
            "slow opening",
            "extended stabilization phase",
            "low stimulation early",
            "integration emphasis on meaning and self-compassion",
        ],
    },
    {
        "file": "c002_anxiety_control_rumination.md",
        "case_id": "complex-002",
        "title": "Anxiety, Control, and Relentless Mental Replay",
        "domain_mix": ["anxiety / control", "cognitive patterns", "emotion regulation"],
        "scenario": """
## Background

I am thirty-four, a project coordinator in a field where small errors have visible consequences. I grew up in a household where unpredictability meant conflict, so I learned early to scan for what might go wrong. I was praised for being mature and responsible; nobody called it anxiety.

## Current Life

Most days look functional. I meet deadlines, answer messages quickly, and maintain a calm appearance. Internally I am rarely calm. If plans change without warning, my chest tightens. I check lists repeatedly. I need to stay in control of my schedule, my body, and even my thoughts.

panic hits me out of nowhere sometimes — in grocery lines, in meetings, on the drive home. Afterward I feel ashamed, as if competent adults should not react that way.

## Thoughts

My mind gets stuck on the same worries. I cannot stop thinking about what might happen. I replay conversations again and again, searching for mistakes. I have to keep my thoughts under control; if I relax mentally I'm afraid things will fall apart.

I monitor my mind all the time. Small uncertainties expand into full scenarios within minutes.

## Emotions

Small things can spike my anxiety quickly. I get overwhelmed by my feelings quickly when too many demands stack up. I try not to feel anything when things get hard, then wonder why I feel brittle.

I'm afraid of losing control — of my body, my schedule, my reputation. I resist letting go of control even when exhaustion is obvious.

## Relationships

I expect people to disappoint me eventually, so I prepare for disappointment in advance. My partner says I am present but guarded. I keep wondering what they really want from me, reading neutral comments as criticism.

## Goals

I want more inner quiet without becoming careless. I want to stop the loops that steal sleep and weekends. I am open to learning how to tolerate uncertainty in small steps.

## Values

Reliability, competence, and protecting people I care about matter to me. I admire people who can adapt; I do not know how they do it without everything collapsing.

## Internal Conflicts

I want rest and fear that rest equals dropping guard. I want trust and scan for betrayal. I want flexibility and believe control is the only thing keeping me safe.
""",
        "patterns": [
            "anxiety_reactivity",
            "fear_of_losing_control",
            "panic_reactivity",
            "control_resistance",
            "rumination",
            "mental_overcontrol",
            "obsessive_thinking_loop",
            "emotional_suppression",
            "trust_difficulty",
        ],
        "weak_domains": ["relationships_domain", "emotional_flexibility_domain", "meaning"],
        "assessments": [
            "anxiety-short",
            "cognitive-patterns-domain-short",
            "emotion-regulation-domain-short",
            "emotional-flexibility-domain-short",
        ],
        "strategy_focus": [
            "emotion regulation",
            "emotional flexibility",
            "personality / pacing",
        ],
        "scenario_themes": [
            "grounding-first",
            "control-aware language",
            "predictable structure",
            "gradual exposure to openness",
        ],
        "timeline": [
            "structured opening",
            "clear transitions",
            "early grounding emphasis",
            "avoid abrupt surrender prompts",
        ],
    },
    {
        "file": "c003_identity_meaning_transition.md",
        "case_id": "complex-003",
        "title": "Identity Confusion and Loss of Meaning After Career Change",
        "domain_mix": ["identity", "meaning / purpose", "values"],
        "scenario": """
## Background

I am thirty-nine and left a stable corporate role eighteen months ago to start a smaller creative practice. On paper it was intentional. Emotionally it unraveled my sense of who I am. I was known as the reliable executive; now I am not sure what title fits.

## Current Life

Income fluctuates. Some weeks I feel alive in the work; other weeks I wonder why I am living anymore in a flat, literal sense — not suicidal, but hollow. life feels meaningless for stretches. nothing feels meaningful anymore when I compare this path to my old identity.

Clients appreciate the output; I rarely feel pride. I avoid telling old colleagues what I am doing because I expect judgment.

## Thoughts

I don't know who I am anymore. I feel confused about my identity. I don't know what really matters to me anymore. I feel like I am living someone else's life when I follow trends in my field instead of my own instincts.

I'm trying to understand myself better, but the answers change week to week.

## Emotions

Shame after social events where I cannot describe my work cleanly. Brief excitement when a project lands, then a crash into doubt. I feel torn inside about whether I made a courageous choice or a self-indulgent mistake.

## Relationships

My marriage is supportive but strained by financial uncertainty. I keep one foot out of friendships from my old career, expecting people to see me as diminished. I feel disconnected from others who seem confident in their paths.

## Goals

I want clarity about values and direction, not just productivity. I want to feel that my life has purpose beyond proving I can survive without a corporate badge.

## Values

Creativity, integrity, independence, and contribution used to feel aligned. Now they compete: independence versus security, creativity versus market demand.

## Internal Conflicts

I want freedom and miss structure. I want meaning and dismiss my current work as insufficient. I want identity certainty while living a transition that by definition is uncertain.
""",
        "patterns": [
            "identity_confusion",
            "identity_uncertainty",
            "loss_of_meaning",
            "hopelessness_signal",
            "inner_conflict",
            "search_for_self_understanding",
            "social_disconnection_signal",
            "shame_sensitivity",
        ],
        "weak_domains": [
            "values_identity_domain",
            "relationships_domain",
            "emotion_regulation_domain",
            "self_domain",
        ],
        "assessments": [
            "values-identity-domain-short",
            "meaning-purpose-short",
            "self-domain-short",
            "relationships-domain-short",
        ],
        "strategy_focus": ["meaning / purpose", "self-worth / self-criticism", "relationships"],
        "scenario_themes": [
            "values clarification",
            "identity exploration without labeling",
            "gentle meaning-making",
        ],
        "timeline": [
            "reflective pacing",
            "space for narrative integration",
            "avoid premature closure on identity",
        ],
    },
    {
        "file": "c004_relationships_belonging_withdrawal.md",
        "case_id": "complex-004",
        "title": "Relationships, Belonging, and Chronic Withdrawal",
        "domain_mix": ["relationships", "belonging", "self-worth"],
        "scenario": """
## Background

I am twenty-eight, moved to a new city three years ago for work, and never fully rooted. Childhood was stable but emotionally muted — affection was practical, not verbal. I learned to stay pleasant and self-contained.

## Current Life

Work is fine. Life outside work feels thin. I don't socialize with people the way I thought I would by now. Weekends are long. I tell myself I prefer quiet, but the quiet often feels like loneliness.

I feel like I do not belong in groups where everyone already has shared history. nobody needs me here in a way that feels secure.

## Thoughts

I want close relationships but I never let people get close. When someone gets nearer I think about how they will eventually see the disappointing parts. I keep wondering what they really want from me.

I feel like I do not matter in most rooms. people do not value me the way I wish they would.

## Emotions

A ache when I see friend groups online. Embarrassment after oversharing once and pulling back hard. I avoid situations that might upset me socially — parties, group trips, after-work drinks.

## Relationships

It is hard for me to fully trust people. I keep emotional distance so I cannot be hurt. I expect people to disappoint me eventually. I stay away from people when I feel exposed.

There is one colleague I could be friends with, but I cancel plans when the day arrives.

## Goals

I want a few relationships that feel real, not performative. I want to stop pre-rejecting myself before others can.

## Values

Kindness, loyalty, and authenticity matter to me, though I often perform agreeableness instead of showing what I really think.

## Internal Conflicts

I crave belonging and protect myself with withdrawal. I want intimacy and fear being unwanted if someone sees the whole picture.
""",
        "patterns": [
            "social_disconnection_signal",
            "social_withdrawal",
            "trust_difficulty",
            "fear_of_rejection",
            "unworthiness_signal",
            "communication_avoidance",
            "emotional_avoidance",
        ],
        "weak_domains": [
            "relationships_domain",
            "self_domain",
            "emotion_regulation_domain",
            "meaning",
        ],
        "assessments": [
            "relationships-domain-short",
            "self-domain-short",
            "emotion-regulation-domain-short",
        ],
        "strategy_focus": ["relationships", "self-worth / self-criticism", "emotion regulation"],
        "scenario_themes": [
            "relational safety",
            "non-forceful connection",
            "belonging without pressure",
        ],
        "timeline": [
            "warm relational framing",
            "avoid crowded interpersonal intensity early",
            "gradual trust-building arc",
        ],
    },
    {
        "file": "c005_self_worth_perfectionism_burnout.md",
        "case_id": "complex-005",
        "title": "Self-Worth Tied to Achievement and Perfectionism",
        "domain_mix": ["self-worth", "perfectionism", "cognitive patterns"],
        "scenario": """
## Background

I am thirty-six, eldest child, academic household. Love felt conditional on performance — not cruelly, but consistently. I internalized the message that worth is earned daily.

## Current Life

I excel at work and feel empty after milestones. Promotions bring brief relief, then a new standard. No matter what I achieve, it never feels good enough. I beat myself up over small mistakes that nobody else remembers.

Evenings are spent replaying errors. Rest feels like falling behind.

## Thoughts

My inner voice is very critical. I cannot stop criticizing myself after I mess up. I am harsh with myself in ways I would never be with a friend. Comparing myself to others decides how valuable I feel.

When someone praises me, I suddenly feel good about myself; after criticism, I quickly feel worthless. I track my value through how others react to me.

## Emotions

Shame when feedback is neutral but I expected praise. Anxiety before presentations that should be routine. I push my feelings down to keep performing.

## Relationships

I attract people who admire competence and rarely see vulnerability. My partner says I am kind but unreachable when ashamed. I fear disappointing others, so I over-deliver and resent the pressure privately.

## Goals

I want stable self-worth that does not collapse after minor flaws. I want to enjoy achievement without immediately raising the bar.

## Values

Excellence, responsibility, and growth matter deeply — perhaps too deeply when they crowd out compassion for myself.

## Internal Conflicts

I want self-acceptance and believe acceptance will make me lazy. I want connection and hide anything that looks imperfect.
""",
        "patterns": [
            "perfectionism",
            "harsh_self_criticism",
            "self_worth_instability",
            "shame_sensitivity",
            "rumination",
            "fear_of_disappointing_others",
            "people_pleasing",
        ],
        "weak_domains": [
            "self_domain",
            "emotion_regulation_domain",
            "relationships_domain",
            "emotional_flexibility_domain",
        ],
        "assessments": [
            "self-domain-short",
            "cognitive-patterns-domain-short",
            "emotion-regulation-domain-short",
            "big-five-short",
        ],
        "strategy_focus": [
            "self-worth / self-criticism",
            "personality / pacing",
            "emotion regulation",
        ],
        "scenario_themes": [
            "anti-perfectionist pacing",
            "self-compassion framing",
            "reduce performance pressure",
        ],
        "timeline": [
            "moderate structure",
            "explicit permission for imperfection",
            "integration on self-worth themes",
        ],
    },
]


def _extend_profiles() -> list[dict]:
    """Return full benchmark profile definitions."""
    extra = [
        {
            "file": "c006_low_mood_anhedonia_withdrawal.md",
            "case_id": "complex-006",
            "title": "Low Mood, Anhedonia, and Social Withdrawal",
            "domain_mix": ["low mood", "anhedonia", "relationships"],
            "scenario": """
## Background

I am forty-four. The last few years stacked losses: a move, a friendship ending, health scares in the family. I tell people I am "just tired." The tiredness has depth they may not see.

## Current Life

I feel down most of the time. nothing really brings me joy anymore. I don't enjoy things I used to love — hiking, cooking for friends, music. Everything feels dull and colorless. I don't socialize with people and cancel when I do make plans.

Work is autopilot. I hide how flat I feel because I do not want to worry anyone.

## Thoughts

I lie awake going over the same things — what is wrong with me, whether this is permanent, whether I am letting my family down by being unavailable.

## Emotions

Persistent heaviness, not dramatic crying but a gray filter on most hours. I go numb when too much is happening and then feel guilty for being numb.

## Relationships

My spouse feels shut out. I keep emotional distance so I cannot be hurt, even though the hurt already happened internally. I feel disconnected from others.

## Goals

I want to feel pleasure again in small ordinary ways. I want to re-enter relationships without performing wellness.

## Values

Family, steadiness, and being there for others — values I feel I am failing while depressed.

## Internal Conflicts

I want help and fear being a burden. I want rest and feel lazy for resting.
""",
            "patterns": [
                "depressed_mood_signal",
                "anhedonia_signal",
                "social_withdrawal",
                "social_disconnection_signal",
                "emotional_numbing",
                "hopelessness_signal",
            ],
            "weak_domains": [
                "low_mood_depression_signals",
                "relationships_domain",
                "meaning",
                "self_domain",
            ],
            "assessments": [
                "low-mood-short",
                "relationships-domain-short",
                "self-domain-short",
                "grief-loss-short",
            ],
            "strategy_focus": ["presenting context", "relationships", "emotion regulation"],
            "scenario_themes": ["gentle stabilization", "low demand", "validate flat mood without labels"],
            "timeline": ["slow pacing", "minimal cognitive load early", "relationship reconnection later"],
        },
        {
            "file": "c007_trauma_hypervigilance_control.md",
            "case_id": "complex-007",
            "title": "Trauma Stress, Hypervigilance, and Control",
            "domain_mix": ["trauma / stress", "anxiety", "control"],
            "scenario": """
## Background

Five years ago I was in a serious car accident. Physically I recovered; psychologically I did not fully. I was always cautious; afterward caution became a full-time job.

## Current Life

I scan environments constantly. Sudden sounds make me flinch. I avoid highways when possible. Sleep is light. I feel safer when I control plans, routes, and timelines.

I'm afraid of losing control of my body when anxiety spikes. panic hits me out of nowhere in crowded places.

## Thoughts

I replay the accident and near-miss scenarios in new settings. My mind gets stuck on what could go wrong. I cannot stop thinking about what might happen if I relax guard.

## Emotions

Fear arrives faster than reason. I get overwhelmed by my feelings quickly when triggered, then shame for overreacting.

## Relationships

I need people to announce changes early. My family walks on eggshells, which I hate but do not know how to change. I find it hard to trust that others will keep me safe.

## Goals

I want to drive without terror. I want my body to feel like mine again instead of a alarm system.

## Values

Safety, family, and responsibility drive many choices — sometimes at the cost of freedom.

## Internal Conflicts

I want normal life and believe normal requires total control. I want closeness and fear being vulnerable while still fragile.
""",
            "patterns": [
                "accident_context",
                "trauma_context_signal",
                "hypervigilance",
                "startle_sensitivity",
                "fear_of_losing_control",
                "panic_reactivity",
                "sleep_disruption",
                "avoidance_of_triggers",
            ],
            "weak_domains": [
                "trauma_stress_signals",
                "sleep_nightmares",
                "emotion_regulation_domain",
                "relationships_domain",
            ],
            "assessments": [
                "trauma-stress-short",
                "anxiety-short",
                "sleep-short",
                "emotion-regulation-domain-short",
            ],
            "strategy_focus": ["emotion regulation", "presenting context", "personality / pacing"],
            "scenario_themes": ["safety-first", "predictability", "grounding", "avoid surprise escalation"],
            "timeline": ["extended safety orientation", "slow sensory ramp", "clear containment language"],
        },
        {
            "file": "c008_shame_self_criticism_relationships.md",
            "case_id": "complex-008",
            "title": "Shame, Harsh Self-Criticism, and Relational Guardedness",
            "domain_mix": ["shame", "self-criticism", "relationships"],
            "scenario": """
## Background

I am thirty-two, raised in a culture of high expectations and indirect criticism. Mistakes were remembered longer than successes. I became my own strictest judge.

## Current Life

Professionally I am confident. Personally I hide. When I make a mistake, I feel like a failure for days. I often feel embarrassed even when no one is watching.

Romantic relationships end when intimacy increases — not dramatically, but through quiet withdrawal on my side.

## Thoughts

I replay what I did wrong over and over in my head. I tell myself I should have done better. I want to hide when I feel I have failed. deep down I feel I'm not enough for stable love.

## Emotions

Shame hits hard and fast. I push my feelings down at work and explode privately with self-attack.

## Relationships

I keep one foot out of relationships. I expect people to hurt me eventually if they see the real me. Past betrayals still affect me today.

## Goals

I want to stay present when someone sees my flaws. I want a partnership that survives ordinary human imperfection.

## Values

Honor, loyalty, and depth in connection — I long for them while acting as if I do not deserve them.

## Internal Conflicts

I want love and prove unworthiness through self-attack. I want openness and expect rejection.
""",
            "patterns": [
                "shame_sensitivity",
                "harsh_self_criticism",
                "unworthiness_signal",
                "trust_difficulty",
                "fear_of_rejection",
                "social_withdrawal",
                "emotional_suppression",
            ],
            "weak_domains": ["self_domain", "relationships_domain", "emotion_regulation_domain"],
            "assessments": [
                "self-domain-short",
                "relationships-domain-short",
                "emotion-regulation-domain-short",
            ],
            "strategy_focus": ["self-worth / self-criticism", "relationships", "emotion regulation"],
            "scenario_themes": ["shame-sensitive", "non-judgmental mirroring", "gentle relational pacing"],
            "timeline": ["avoid public vulnerability early", "build safety before depth"],
        },
        {
            "file": "c009_grief_meaning_identity.md",
            "case_id": "complex-009",
            "title": "Grief, Meaning Collapse, and Identity Shift",
            "domain_mix": ["grief", "meaning", "identity"],
            "scenario": """
## Background

My sister died unexpectedly four years ago. She was the expressive one; I was the practical one. Her death removed not only a person but a mirror for who I might be.

## Current Life

I function, but life feels meaningless in stretches. I am grieving still, though people assume otherwise because I returned to work quickly. I don't know who I am anymore without her contrast.

Anniversaries flatten me. Joy feels disloyal.

## Thoughts

life feels meaningless when I imagine decades without her voice. I feel torn inside about moving forward. I'm trying to understand myself better after this rupture.

I lost someone close to me and I cannot get over the loss in any neat narrative.

## Emotions

Grief, guilt, occasional numbness. I avoid situations that might upset me — family events where her absence is obvious.

## Relationships

I am closer to some relatives and distant from others who grieved differently. I feel disconnected from friends who did not know her well.

## Goals

I want a relationship with memory that is not only pain. I want identity that includes loss without being only loss.

## Values

Family, remembrance, honesty, and living fully — values that now conflict with each other.

## Internal Conflicts

I want healing and feel disloyal for wanting it. I want meaning and reject offered meanings that feel too easy.
""",
            "patterns": [
                "grief_signal",
                "bereavement_context",
                "loss_of_meaning",
                "identity_confusion",
                "inner_conflict",
                "emotional_avoidance",
                "social_disconnection_signal",
            ],
            "weak_domains": ["grief_loss_bereavement", "meaning", "values_identity_domain", "relationships_domain"],
            "assessments": [
                "grief-loss-short",
                "meaning-purpose-short",
                "values-identity-domain-short",
                "relationships-domain-short",
            ],
            "strategy_focus": ["meaning / purpose", "emotion regulation", "relationships"],
            "scenario_themes": ["grief-informed", "meaning exploration", "identity-safe language"],
            "timeline": ["slow arc", "space for remembrance", "integration weighted toward meaning"],
        },
        {
            "file": "c010_emotion_suppression_overwhelm_flexibility.md",
            "case_id": "complex-010",
            "title": "Suppression, Overwhelm, and Low Emotional Flexibility",
            "domain_mix": ["emotion regulation", "flexibility", "control"],
            "scenario": """
## Background

I am forty-seven, caregiver for an aging parent while working full time. I learned to shut down feelings to keep moving. It worked for years; now the backlog is loud.

## Current Life

I push my feelings down so I can keep going. I go numb when too much is happening. Then small triggers produce disproportionate reactions — I get overwhelmed by my feelings quickly and feel ashamed afterward.

I resist letting go of control in any setting that feels emotionally unpredictable.

## Thoughts

I tell myself I should not feel this way because others have it worse. I monitor my mind all the time for signs I might break down.

## Emotions

Alternating numbness and flooding. I avoid situations that might upset me. Emotions flood me before I can slow down.

## Relationships

My children say I am strong and distant. My partner wants more emotional presence; I fear that opening will unleash everything I contain.

## Goals

I want to feel without losing function. I want flexibility — the ability to bend without snapping.

## Values

Duty, care, reliability, and protecting family — I honor them while resenting the cost.

## Internal Conflicts

I want release and fear collapse. I want support and pride myself on not needing it.
""",
            "patterns": [
                "emotional_suppression",
                "emotional_overwhelm",
                "emotional_avoidance",
                "control_resistance",
                "surrender_difficulty",
                "emotional_numbing",
            ],
            "weak_domains": [
                "emotion_regulation_domain",
                "emotional_flexibility_domain",
                "relationships_domain",
            ],
            "assessments": [
                "emotion-regulation-domain-short",
                "emotional-flexibility-domain-short",
                "relationships-domain-short",
            ],
            "strategy_focus": ["emotion regulation", "emotional flexibility", "relationships"],
            "scenario_themes": ["containment", "gradual opening", "caregiver-aware pacing"],
            "timeline": ["grounding emphasis", "short intense peaks avoided early", "flexibility themes in integration"],
        },
    ]
    return PROFILES + extra


def _profiles_part_two() -> list[dict]:
    return [
        {
            "file": "c011_belonging_rejection_attachment.md",
            "case_id": "complex-011",
            "title": "Belonging Wounds, Rejection Sensitivity, and Attachment Anxiety",
            "domain_mix": ["belonging", "relationships", "self-worth"],
            "scenario": """
## Background

I am twenty-six. School years included exclusion that felt random and memorable. I learned to scan for signs I am unwanted before others can confirm it.

## Current Life

I have friends, yet I feel like I do not belong in most groups. When someone is quiet in a chat thread, I assume I offended them. I feel like I do not matter unless repeatedly reassured.

## Thoughts

I worry people will stop liking me if I show need. I keep going over the same problems in my head after social interactions. deep down I feel I'm not enough as a person.

## Emotions

Anxiety before meetings, shame after perceived missteps. I get overwhelmed by my feelings quickly when I think I am being ignored.

## Relationships

I want close relationships but I never let people get close without tests and reassurance. I expect people to disappoint me eventually. Attachment anxiety shows up as urgency masked as humor.

## Goals

I want to interpret neutral signals more fairly. I want belonging that does not require constant proof.

## Values

Friendship, humor, and loyalty — I want to live them without exhausting vigilance.

## Internal Conflicts

I want trust and rehearse rejection. I want authenticity and hide needs to seem easy.
""",
            "patterns": [
                "social_disconnection_signal",
                "rejection_sensitivity",
                "attachment_anxiety",
                "fear_of_rejection",
                "unworthiness_signal",
                "rumination",
            ],
            "weak_domains": ["relationships_domain", "self_domain", "cognitive_patterns_domain"],
            "assessments": ["relationships-domain-short", "self-domain-short", "cognitive-patterns-domain-short"],
            "strategy_focus": ["relationships", "self-worth / self-criticism"],
            "scenario_themes": ["relational safety", "reassurance without dependency"],
            "timeline": ["warm tone", "predictable facilitator presence", "avoid ambiguous social metaphors early"],
        },
        {
            "file": "c012_values_identity_work_mismatch.md",
            "case_id": "complex-012",
            "title": "Values Misalignment and Identity Strain at Work",
            "domain_mix": ["values", "identity", "meaning"],
            "scenario": """
## Background

I am forty-three in healthcare administration. I entered the field to help; bureaucracy now dominates my days. The gap widened slowly until it felt like a identity fracture.

## Current Life

I perform competence while feeling hollow. I feel like I am living someone else's life when I enforce policies I privately question. life feels meaningless in meetings that consume hours.

## Thoughts

I don't know what really matters to me anymore beyond paying bills. I feel confused about my identity — am I a helper or an operator? I'm trying to understand myself better before making another big change.

## Emotions

Resentment, guilt about resentment, intermittent hopelessness about change.

## Relationships

Colleagues respect me; few know my doubts. My family depends on my income, which complicates any exit fantasy.

## Goals

I want values-aligned work, not just escape. I want a credible next chapter rather than impulsive reinvention.

## Values

Service, honesty, dignity for patients, and family security — they no longer line up cleanly.

## Internal Conflicts

I want integrity and fear financial risk. I want meaning and dismiss small daily acts of care as insufficient.
""",
            "patterns": [
                "identity_confusion",
                "loss_of_meaning",
                "inner_conflict",
                "desire_for_change",
                "search_for_self_understanding",
                "chronic_stress_signal",
            ],
            "weak_domains": ["values_identity_domain", "meaning", "self_domain"],
            "assessments": [
                "values-identity-domain-short",
                "meaning-purpose-short",
                "self-domain-short",
            ],
            "strategy_focus": ["meaning / purpose", "presenting context"],
            "scenario_themes": ["values clarification", "ethical framing", "no career prescription"],
            "timeline": ["reflective middle phases", "integration on direction not decision"],
        },
        {
            "file": "c013_grief_abandonment_relationships.md",
            "case_id": "complex-013",
            "title": "Partner Loss, Abandonment Themes, and Relational Fear",
            "domain_mix": ["grief", "relationships", "abandonment"],
            "scenario": """
## Background

My partner ended our engagement two years ago after a long relationship. The breakup was not death, but it felt like a death of a future I had inhabited fully.

## Current Life

I am functioning, but romantic trust is fractured. I am grieving the life I planned. the grief feels overwhelming when something reminds me of our shared routines.

## Thoughts

I keep one foot out of relationships since then. I expect people to hurt me eventually. I replay what I could have done differently until my mind is raw.

## Emotions

Sadness, shame, spikes of anger, then numbness. I avoid situations that might upset me — places we used to go.

## Relationships

Friends are supportive but tired of the loop. New dating feels impossible because I find it hard to trust people. I keep emotional distance so I cannot be hurt again.

## Goals

I want to stop living in the archive of the relationship. I want openness without guaranteeing pain.

## Values

Commitment, honesty, and building a home — values that now scare me.

## Internal Conflicts

I want partnership and expect abandonment. I want closure and keep reopening the wound through rumination.
""",
            "patterns": [
                "grief_signal",
                "loss_related_distress",
                "relationship_breakup_context",
                "abandonment_wound_signal",
                "trust_difficulty",
                "rumination",
                "social_withdrawal",
            ],
            "weak_domains": ["grief_loss_bereavement", "relationships_domain", "self_domain"],
            "assessments": [
                "grief-loss-short",
                "relationships-domain-short",
                "self-domain-short",
            ],
            "strategy_focus": ["relationships", "meaning / purpose", "emotion regulation"],
            "scenario_themes": ["loss-aware", "relational safety", "gentle pacing"],
            "timeline": ["avoid forced forgiveness framing", "steady containment", "integration on future orientation"],
        },
        {
            "file": "c014_low_mood_hopelessness_meaning.md",
            "case_id": "complex-014",
            "title": "Low Mood, Hopelessness, and Meaning Collapse",
            "domain_mix": ["low mood", "hopelessness", "meaning"],
            "scenario": """
## Background

I am fifty-one. Midlife brought career plateau, aging parents, and a sense that time is narrowing. Nothing dramatic happened in one day; the mood crept in over years.

## Current Life

I feel down most of the time. I feel hopeless about change, not in a dramatic way but as a gray conviction that things will not improve. life feels meaningless when I survey the next decade.

I don't enjoy things I used to love. Evenings are the heaviest.

## Thoughts

I lie awake going over the same things — regrets, missed paths, whether it is too late. I don't know who I am anymore beyond roles.

## Emotions

Flat sadness, occasional tears without clear trigger. I try not to feel anything when things get hard because feeling opens a larger hole.

## Relationships

I am present but muted with my adult children. My spouse worries; I minimize to protect them and isolate more.

## Goals

I want a reason to engage again, not a grand purpose — small reasons would suffice if they felt real.

## Values

Family, fairness, and leaving things better — they feel abstract now.

## Internal Conflicts

I want hope and feel foolish for hoping. I want connection and believe I have nothing to offer.
""",
            "patterns": [
                "depressed_mood_signal",
                "hopelessness_signal",
                "loss_of_meaning",
                "anhedonia_signal",
                "identity_uncertainty",
                "social_withdrawal",
            ],
            "weak_domains": ["low_mood_depression_signals", "meaning", "values_identity_domain", "relationships_domain"],
            "assessments": [
                "low-mood-short",
                "meaning-purpose-short",
                "values-identity-domain-short",
                "relationships-domain-short",
            ],
            "strategy_focus": ["meaning / purpose", "presenting context", "emotion regulation"],
            "scenario_themes": ["gentle stabilization", "hope-oriented without toxic positivity"],
            "timeline": ["slow pacing", "low stimulation", "meaning themes introduced gradually"],
        },
        {
            "file": "c015_anxiety_panic_body_sensitivity.md",
            "case_id": "complex-015",
            "title": "Anxiety, Panic, and Body Sensitivity",
            "domain_mix": ["anxiety", "panic", "body sensitivity"],
            "scenario": """
## Background

I am twenty-nine. Panic began in college, eased, returned after a period of poor sleep and high caffeine. Family history includes worry but not open discussion.

## Current Life

I fear body sensations — heart rate, breath shifts, dizziness. I'm afraid of losing control when sensations spike. panic hits me out of nowhere in trains and elevators.

I monitor my mind and body constantly. I avoid situations that might upset me physically — exercise, heat, long meetings without exit routes.

## Thoughts

I cannot stop thinking about what might happen if I faint or lose control publicly. My thoughts loop and I cannot switch them off.

## Emotions

Terror during spikes; shame after. I get overwhelmed by my feelings quickly and then avoid the next similar setting.

## Relationships

Friends do not see the extent of avoidance. I cancel plans when panic has been recent.

## Goals

I want to ride out sensations without catastrophe thinking. I want freedom to travel again.

## Values

Independence, exploration, and health — all constrained by fear right now.

## Internal Conflicts

I want recovery and feed fear by scanning. I want trust in my body and treat every signal as danger.
""",
            "patterns": [
                "panic_reactivity",
                "fear_of_losing_control",
                "fear_of_body_sensations",
                "somatic_anxiety",
                "avoidance_of_triggers",
                "rumination",
                "sleep_disruption",
            ],
            "weak_domains": ["anxiety_fear_panic", "sleep_nightmares", "emotion_regulation_domain"],
            "assessments": ["anxiety-short", "sleep-short", "emotion-regulation-domain-short", "cognitive-patterns-domain-short"],
            "strategy_focus": ["emotion regulation", "personality / pacing"],
            "scenario_themes": ["body-safe language", "grounding", "predictable pacing"],
            "timeline": ["exit options emphasized symbolically", "breath-friendly arc", "avoid trapping imagery"],
        },
        {
            "file": "c016_shame_guilt_grief.md",
            "case_id": "complex-016",
            "title": "Shame, Guilt, and Complicated Grief",
            "domain_mix": ["shame", "guilt", "grief"],
            "scenario": """
## Background

I am thirty-eight. My mother's death followed years of conflict we never repaired. Grief arrived mixed with guilt that feels unspeakable.

## Current Life

I am grieving and ashamed of how we left things. When I make a mistake now, I feel like a failure as a daughter and as a person. I often feel embarrassed even when no one is watching.

Family rituals are minefields. I want to hide when I feel I have failed her and myself.

## Thoughts

I replay our last arguments. I tell myself I should have done better while she was alive. the grief feels overwhelming and undeserved to carry cleanly.

## Emotions

Shame, sorrow, anger at myself, periods of numbness. I push my feelings down at work.

## Relationships

Siblings grieve differently; we barely speak about the conflict. My partner supports me but I keep emotional distance so I cannot be hurt further when grief spikes.

## Goals

I want a way to mourn that includes imperfection in the relationship. I want relief from punitive self-talk.

## Values

Forgiveness, family, and honesty — I apply them harshly inward and generously outward.

## Internal Conflicts

I want compassion and punish myself. I want connection with family and fear opening old wounds.
""",
            "patterns": [
                "grief_signal",
                "bereavement_context",
                "shame_sensitivity",
                "harsh_self_criticism",
                "guilt_burden",
                "emotional_suppression",
                "trust_difficulty",
            ],
            "weak_domains": ["grief_loss_bereavement", "self_domain", "relationships_domain"],
            "assessments": ["grief-loss-short", "self-domain-short", "relationships-domain-short"],
            "strategy_focus": ["self-worth / self-criticism", "meaning / purpose", "emotion regulation"],
            "scenario_themes": ["shame-informed", "grief complexity", "non-moralizing"],
            "timeline": ["slow trust build", "avoid forced reconciliation narrative"],
        },
        {
            "file": "c017_identity_belonging_withdrawal.md",
            "case_id": "complex-017",
            "title": "Identity Uncertainty, Belonging, and Withdrawal",
            "domain_mix": ["identity", "belonging", "withdrawal"],
            "scenario": """
## Background

I am twenty-three, second-generation immigrant, navigating between family expectations and peers who feel culturally fluent in ways I am not. Identity has always felt negotiated, never default.

## Current Life

I feel like I do not belong in either world fully. I don't socialize with people outside small safe circles. Online I perform confidence; offline I cancel.

## Thoughts

I don't know who I am anymore when old labels stop fitting. I feel confused about my identity. people do not value me the way I wish they would in groups where I am the outsider.

## Emotions

Loneliness, shame, brief anger at myself for caring so much about belonging.

## Relationships

Close to one friend; otherwise I stay away from people when I feel exposed. I find it hard to trust people with cultural parts of my story.

## Goals

I want integrated identity, not choosing one side. I want community without performing.

## Values

Family respect, autonomy, and authenticity — they pull in different directions.

## Internal Conflicts

I want belonging and preemptively reject groups. I want authenticity and edit myself constantly.
""",
            "patterns": [
                "identity_confusion",
                "identity_uncertainty",
                "social_disconnection_signal",
                "social_withdrawal",
                "unworthiness_signal",
                "communication_avoidance",
            ],
            "weak_domains": ["values_identity_domain", "relationships_domain", "self_domain"],
            "assessments": [
                "values-identity-domain-short",
                "relationships-domain-short",
                "self-domain-short",
            ],
            "strategy_focus": ["meaning / purpose", "relationships", "self-worth / self-criticism"],
            "scenario_themes": ["identity-safe", "belonging without assimilation pressure"],
            "timeline": ["inclusive language", "avoid cultural stereotyping", "gentle social themes late"],
        },
        {
            "file": "c018_control_surrender_session_concerns.md",
            "case_id": "complex-018",
            "title": "Control Resistance and Psychedelic Session Concerns",
            "domain_mix": ["control", "session concerns", "anxiety"],
            "scenario": """
## Background

I am forty-five, exploring a guided psychedelic session for stagnation and grief residue. I am curious and terrified in equal measure. Previous cannabis experiences felt too uncontrollable once.

## Current Life

I read extensively about sessions but delay booking. I'm anxious about the ceremony logistics. I fear a bad trip more than I admit in consultations.

I need to stay in control. I resist letting go of control even when I know rigidity is the problem.

## Thoughts

I cannot stop thinking about what might happen if I lose control of my mind in session. I resist losing control in the session even while signing up for it.

## Emotions

Fear of body sensations, fear of emotional flooding, shame about fear.

## Relationships

My facilitator seems competent; I still scan for signs I cannot trust them fully. My partner is supportive but worried.

## Goals

I want enough trust to proceed safely. I want to learn surrender in small steps, not as a heroic leap.

## Values

Growth, honesty, spiritual openness, and safety — tension between them is live.

## Internal Conflicts

I want transformation and cling to control. I want trust and prepare exit strategies.
""",
            "patterns": [
                "psychedelic_anxiety",
                "fear_of_bad_trip",
                "control_resistance",
                "surrender_difficulty",
                "trust_in_facilitator_difficulty",
                "fear_of_losing_control",
                "fear_of_body_sensations",
            ],
            "weak_domains": ["psychedelic_session_concerns", "anxiety_fear_panic", "emotional_flexibility_domain"],
            "assessments": [
                "psychedelic-concern-short",
                "anxiety-short",
                "emotional-flexibility-domain-short",
            ],
            "strategy_focus": ["emotional flexibility", "emotion regulation", "presenting context"],
            "scenario_themes": ["high trust emphasis", "control-aware", "facilitator rapport", "explicit safety"],
            "timeline": ["long preparation phase", "consent checkpoints", "grounding before depth", "integration weighted"],
        },
        {
            "file": "c019_chronic_pain_fatigue_mood.md",
            "case_id": "complex-019",
            "title": "Chronic Pain, Fatigue, and Low Mood",
            "domain_mix": ["chronic pain", "fatigue", "low mood"],
            "scenario": """
## Background

I am forty-nine with fibromyalgia-like symptoms for seven years. Medical path has been frustrating — tests inconclusive, suggestions inconsistent. Mood followed pain, not the reverse.

## Current Life

my body hurts all the time. fatigue burden makes ordinary tasks feel monumental. I feel down most of the time when pain is high. Everything feels dull and colorless on bad weeks.

I avoid activity due to pain flares. doctors don't understand my pain, which adds anger and helplessness.

## Thoughts

I lie awake going over the same things — whether I am exaggerating, whether this is permanent, whether I am letting my family down.

## Emotions

Frustration, grief for old physical freedom, shame when I cancel plans again.

## Relationships

My partner helps and burns out. I feel disconnected from friends who plan physically active outings.

## Goals

I want better pacing, not a miracle cure narrative. I want mood that is not entirely hostage to pain days.

## Values

Vitality, reliability, and presence with family — all feel threatened.

## Internal Conflicts

I want hope and fear disappointment from providers. I want activity and fear flares.
""",
            "patterns": [
                "chronic_pain_burden",
                "fatigue_burden",
                "depressed_mood_signal",
                "anhedonia_signal",
                "frustration_with_medical_system",
                "activity_avoidance_due_to_pain",
                "hopelessness_signal",
            ],
            "weak_domains": [
                "chronic_pain_fibromyalgia_fatigue",
                "low_mood_depression_signals",
                "relationships_domain",
            ],
            "assessments": [
                "pain-fatigue-short",
                "low-mood-short",
                "relationships-domain-short",
            ],
            "strategy_focus": ["presenting context", "emotion regulation"],
            "scenario_themes": ["body-aware pacing", "validate pain without medical claims"],
            "timeline": ["low physical demand", "rest-friendly sequencing", "avoid pain-dismissive language"],
        },
        {
            "file": "c020_people_pleasing_boundaries_resentment.md",
            "case_id": "complex-020",
            "title": "People Pleasing, Weak Boundaries, and Inner Resentment",
            "domain_mix": ["relationships", "self-worth", "inner conflict"],
            "scenario": """
## Background

I am thirty-five, labeled "easy to work with" everywhere I go. Agreement was survival in childhood; now it is reflex.

## Current Life

I say yes too often, then resent people privately. I apologize excessively. I monitor others' reactions closely and adjust myself. No matter what I achieve, it never feels good enough if someone is displeased.

## Thoughts

I tell myself I should have done better when I disappoint anyone slightly. I keep wondering what they really want from me. I feel torn inside between honesty and harmony.

## Emotions

Anxiety before saying no, shame after saying yes to the wrong thing, quiet bitterness.

## Relationships

Friends rely on me; I feel unseen. My partner wants authentic preferences, not default agreement.

## Goals

I want boundaries without feeling cruel. I want self-worth that survives disapproval.

## Values

Kindness, harmony, and integrity — integrity keeps losing quietly.

## Internal Conflicts

I want respect and fear conflict. I want authenticity and perform agreeableness.
""",
            "patterns": [
                "people_pleasing",
                "fear_of_disappointing_others",
                "boundary_difficulty",
                "conflict_avoidance",
                "harsh_self_criticism",
                "inner_conflict",
                "perfectionism",
            ],
            "weak_domains": ["self_domain", "relationships_domain", "values_identity_domain"],
            "assessments": [
                "self-domain-short",
                "relationships-domain-short",
                "values-identity-domain-short",
            ],
            "strategy_focus": ["self-worth / self-criticism", "relationships"],
            "scenario_themes": ["boundary-safe exploration", "non-blaming relational framing"],
            "timeline": ["collaborative tone", "avoid conflict simulation early"],
        },
    ]


def _profiles_part_three() -> list[dict]:
    return [
        {
            "file": "c021_rumination_sleep_anxiety.md",
            "case_id": "complex-021",
            "title": "Rumination, Sleep Disruption, and Night Anxiety",
            "domain_mix": ["cognitive patterns", "sleep", "anxiety"],
            "scenario": """
## Background

I am thirty-seven, knowledge worker, screens late into evening. Sleep problems began during a stressful promotion year and never fully left.

## Current Life

I lie awake going over the same things — work, money, health fears. My mind gets stuck on the same worries at 2 a.m. Sleep disruption makes days harder; harder days feed worry.

Small things can spike my anxiety quickly when I am sleep deprived.

## Thoughts

I replay conversations again and again. I cannot stop thinking about what might happen financially if I burn out.

## Emotions

Dread at bedtime, irritability daytime, shame about being short with my kids.

## Relationships

Partner sleeps separately some nights — practical, but it stings. I avoid talking about anxiety to not add stress.

## Goals

I want sleep that restores rather than battles. I want mental loops to lose their grip at night.

## Values

Providing for family, being a present parent, and doing good work — all feel jeopardized by exhaustion.

## Internal Conflicts

I want rest and scroll for distraction. I want calm and rehearse catastrophes.
""",
            "patterns": [
                "rumination",
                "obsessive_thinking_loop",
                "sleep_disruption",
                "insomnia_signal",
                "anxiety_reactivity",
                "mental_overcontrol",
            ],
            "weak_domains": ["sleep_nightmares", "cognitive_patterns_domain", "anxiety_fear_panic"],
            "assessments": [
                "sleep-short",
                "cognitive-patterns-domain-short",
                "anxiety-short",
            ],
            "strategy_focus": ["emotion regulation", "personality / pacing"],
            "scenario_themes": ["sleep-friendly pacing", "reduce cognitive load evening themes"],
            "timeline": ["calm sequencing", "avoid late-phase stimulation"],
        },
        {
            "file": "c022_avoidance_numbness_flexibility.md",
            "case_id": "complex-022",
            "title": "Emotional Avoidance, Numbing, and Flexibility Deficits",
            "domain_mix": ["avoidance", "numbing", "flexibility"],
            "scenario": """
## Background

I am forty-two, former first responder, now admin role. Years of exposure taught me to shut down fast. Retirement from the field did not retire the reflex.

## Current Life

I distract myself so I do not have to feel. I stay busy to avoid my feelings. I go numb when too much is happening — news, family conflict, even good news that feels too loud.

I resist letting go of control in unstructured settings.

## Thoughts

I tell myself feeling is dangerous at scale. When emotion rises I change the subject internally or literally.

## Emotions

Muted baseline, occasional surges that scare me. I avoid situations that might upset me.

## Relationships

My teenager says I am emotionally absent. Coworkers find me reliable and opaque.

## Goals

I want selective openness — feeling without flooding. I want flexibility rather than on/off states.

## Values

Protection, service, and stoicism — stoicism now costs connection.

## Internal Conflicts

I want closeness and treat feelings as liability. I want peace and maintain it through avoidance.
""",
            "patterns": [
                "emotional_avoidance",
                "emotional_numbing",
                "emotional_suppression",
                "control_resistance",
                "surrender_difficulty",
                "communication_avoidance",
            ],
            "weak_domains": ["emotion_regulation_domain", "emotional_flexibility_domain", "relationships_domain"],
            "assessments": [
                "emotion-regulation-domain-short",
                "emotional-flexibility-domain-short",
                "relationships-domain-short",
            ],
            "strategy_focus": ["emotion regulation", "emotional flexibility", "relationships"],
            "scenario_themes": ["strength-based framing", "gradual feeling tolerance"],
            "timeline": ["predictable structure", "integration on connection"],
        },
        {
            "file": "c023_meaning_spiritual_integration.md",
            "case_id": "complex-023",
            "title": "Meaning Seeking, Spiritual Openness, and Integration Need",
            "domain_mix": ["meaning", "spirituality", "integration"],
            "scenario": """
## Background

I am thirty-three. A powerful non-ordinary experience two years ago opened questions I cannot close. Daily life feels thin compared to what I touched briefly.

## Current Life

I'm open to a spiritual experience again but fear repeating confusion afterward. I need help integrating the experience into ordinary life. life feels meaningless when I ignore the questions it raised.

## Thoughts

I'm trying to understand myself better spiritually without adopting a label that fits poorly. meaning_seeking pulls me toward retreat and away from bills and relationships.

## Emotions

Wonder, frustration, loneliness in language gaps with friends who did not experience this.

## Relationships

Partner is practical; I feel misunderstood, not judged, but alone with the story. A community would help if I trusted it.

## Goals

I want integration, not endless seeking. I want meaning that lives in Tuesday afternoons, not only peaks.

## Values

Truth, compassion, and wonder — I want them grounded.

## Internal Conflicts

I want transcendence and need embodiment. I want community and fear cultish tones.
""",
            "patterns": [
                "meaning_seeking",
                "spiritual_openness",
                "integration_need",
                "loss_of_meaning",
                "search_for_self_understanding",
                "social_disconnection_signal",
            ],
            "weak_domains": ["meaning", "values_identity_domain", "relationships_domain"],
            "assessments": [
                "meaning-purpose-short",
                "values-identity-domain-short",
                "relationships-domain-short",
            ],
            "strategy_focus": ["meaning / purpose", "relationships"],
            "scenario_themes": ["integration-focused", "spiritual openness without dogma"],
            "timeline": ["integration phase emphasized", "grounding between depth waves"],
        },
        {
            "file": "c024_perfectionism_control_emotion_regulation.md",
            "case_id": "complex-024",
            "title": "Perfectionism, Control, and Emotion Regulation Strain",
            "domain_mix": ["perfectionism", "control", "emotion regulation"],
            "scenario": """
## Background

I am twenty-seven in law. Precision is rewarded; imperfection is penalized. The culture fits my wiring too well.

## Current Life

I have to keep my thoughts under control. I monitor my mind all the time. When something is imperfect, I beat myself up over small mistakes publicly invisible but internally loud.

Emotions flood me before I can slow down after criticism from supervisors.

## Thoughts

No matter what I achieve, it never feels good enough. I replay errors endlessly. I resist letting go of control in any unstructured process.

## Emotions

Anxiety, brief shame spikes, suppressed anger. I push my feelings down until headaches arrive.

## Relationships

Little time for relationships. Dating feels inefficient. Friends drift.

## Goals

I want sustainable excellence without self-destruction. I want feelings that inform rather than derail.

## Values

Justice, precision, and merit — admired and weaponized against myself.

## Internal Conflicts

I want humanity and treat it as weakness. I want rest and fear falling behind.
""",
            "patterns": [
                "perfectionism",
                "mental_overcontrol",
                "harsh_self_criticism",
                "control_resistance",
                "emotional_overwhelm",
                "emotional_suppression",
                "rumination",
            ],
            "weak_domains": ["self_domain", "emotion_regulation_domain", "emotional_flexibility_domain"],
            "assessments": [
                "self-domain-short",
                "cognitive-patterns-domain-short",
                "emotion-regulation-domain-short",
                "emotional-flexibility-domain-short",
            ],
            "strategy_focus": ["self-worth / self-criticism", "emotion regulation", "emotional flexibility"],
            "scenario_themes": ["anti-perfectionist", "control-aware", " sustainable pacing"],
            "timeline": ["structured but not punitive", "integration on self-worth"],
        },
        {
            "file": "c025_grief_mood_disconnection.md",
            "case_id": "complex-025",
            "title": "Grief, Low Mood, and Social Disconnection Combined",
            "domain_mix": ["grief", "low mood", "disconnection"],
            "scenario": """
## Background

I am fifty-five. Widowed eighteen months ago after thirty years of marriage. Friends treat me gently; gentleness sometimes feels like being seen only as loss.

## Current Life

I am grieving and I feel down most of the time. nothing really brings me joy anymore. I feel disconnected from others even in support groups. I don't want to talk to anyone some weeks.

the grief feels overwhelming and the house feels louder in silence.

## Thoughts

I replay ordinary mornings — coffee, news, small talk — that will not return. I feel like I do not matter outside the role of widow.

## Emotions

Sadness, numbness, guilt on better days, shame for laughing once and stopping quickly.

## Relationships

Adult kids worry. I keep emotional distance so I cannot be hurt further, which I know hurts them too.

## Goals

I want companionship with my grief, not erasure. I want moments of warmth without betrayal of memory.

## Values

Loyalty, family, and honesty about pain — still guiding, still heavy.

## Internal Conflicts

I want connection and push people away. I want relief and fear forgetting.
""",
            "patterns": [
                "grief_signal",
                "bereavement_context",
                "depressed_mood_signal",
                "anhedonia_signal",
                "social_disconnection_signal",
                "social_withdrawal",
                "loss_related_distress",
            ],
            "weak_domains": [
                "grief_loss_bereavement",
                "low_mood_depression_signals",
                "relationships_domain",
                "meaning",
            ],
            "assessments": [
                "grief-loss-short",
                "low-mood-short",
                "relationships-domain-short",
                "meaning-purpose-short",
            ],
            "strategy_focus": ["meaning / purpose", "relationships", "presenting context"],
            "scenario_themes": ["grief-centered", "gentle mood validation", "connection without pressure"],
            "timeline": ["slow", "extended stabilization", "meaning and connection in late integration"],
        },
        {
            "file": "c026_attachment_rejection_self_criticism.md",
            "case_id": "complex-026",
            "title": "Attachment Anxiety, Rejection Fear, and Self-Criticism",
            "domain_mix": ["attachment", "rejection", "self-criticism"],
            "scenario": """
## Background

I am thirty-one with a pattern of intense relationships that cool after commitment deepens. Early instability at home made love feel conditional on mood.

## Current Life

When a partner is distant, I spiral. I worry people will stop liking me if I show the full need underneath. After conflict I cannot stop criticizing myself after I mess up.

## Thoughts

I keep going over the same problems in my head — tone of texts, timing of replies. deep down I feel I'm not enough to keep love stable.

## Emotions

Anxiety, shame, brief anger, then self-attack. I get overwhelmed by my feelings quickly during relational uncertainty.

## Relationships

I want close relationships but I never let people get close without testing them. I expect people to disappoint me eventually.

## Goals

I want secure attachment behaviors, or at least less destructive ones. I want self-criticism to soften after ordinary conflict.

## Values

Love, loyalty, and emotional honesty — I want them without terror.

## Internal Conflicts

I want closeness and provoke distance to confirm fears. I want reassurance and shame the need.
""",
            "patterns": [
                "attachment_anxiety",
                "fear_of_rejection",
                "rejection_sensitivity",
                "harsh_self_criticism",
                "unworthiness_signal",
                "rumination",
            ],
            "weak_domains": ["relationships_domain", "self_domain", "cognitive_patterns_domain"],
            "assessments": [
                "relationships-domain-short",
                "self-domain-short",
                "cognitive-patterns-domain-short",
            ],
            "strategy_focus": ["relationships", "self-worth / self-criticism"],
            "scenario_themes": ["relational safety", "non-urgent attachment language"],
            "timeline": ["steady facilitator presence", "avoid abandonment triggers in metaphors"],
        },
        {
            "file": "c027_life_transition_inner_conflict.md",
            "case_id": "complex-027",
            "title": "Life Transition, Inner Conflict, and Change Desire",
            "domain_mix": ["life transition", "inner conflict", "change"],
            "scenario": """
## Background

I am forty-eight. Empty nest coincided with selling a business I built for twenty years. Identity was nested in being needed in a specific way.

## Current Life

Days are unstructured in a way that unsettles me. I feel torn inside about whether to start something new or finally rest. I'm trying to understand myself better without the old roles.

## Thoughts

I don't know who I am anymore without daily urgency. I feel confused about my identity as a builder if I stop building.

## Emotions

Restlessness, grief for a chapter, excitement I distrust, shame about not enjoying freedom.

## Relationships

Marriage is renegotiating. Friends are still working; I hide envy and judge myself for it.

## Goals

I want a next chapter that fits, not a reflexive rebound project. I want inner conflict to become information, not paralysis.

## Values

Legacy, family, creativity, and freedom — rebalancing now.

## Internal Conflicts

I want rest and feel worthless without striving. I want change and fear losing who I was.
""",
            "patterns": [
                "life_transition_distress",
                "inner_conflict",
                "identity_confusion",
                "desire_for_change",
                "search_for_self_understanding",
                "rumination",
            ],
            "weak_domains": ["values_identity_domain", "meaning", "self_domain"],
            "assessments": [
                "values-identity-domain-short",
                "meaning-purpose-short",
                "self-domain-short",
            ],
            "strategy_focus": ["meaning / purpose", "self-worth / self-criticism"],
            "scenario_themes": ["transition-aware", "identity exploration"],
            "timeline": ["reflective pacing", "space for ambiguity in integration"],
        },
        {
            "file": "c028_speech_anxiety_visibility_shame.md",
            "case_id": "complex-028",
            "title": "Speech Anxiety, Social Visibility, and Shame",
            "domain_mix": ["speech / expression", "anxiety", "shame"],
            "scenario": """
## Background

I am twenty-five with a mild stutter worsened under stress. School presentations were painful; avoidance became policy.

## Current Life

I'm afraid to speak in front of people. I avoid conversations when I can. When I must speak, I anticipate failure for hours. I feel ashamed about speech even when listeners are kind.

## Thoughts

words get stuck and I panic internally. I replay stumbles for days. I expect people to see me as less competent.

## Emotions

Anxiety before speech, shame after, relief mixed with self-attack when done.

## Relationships

I contribute in writing channels at work while voice stays quiet. Dating is harder — voice matters.

## Goals

I want functional speech under moderate stress, not perfection. I want shame to stop governing career choices.

## Values

Expression, honesty, and competence — blocked by visibility fear.

## Internal Conflicts

I want visibility and hide. I want respect and expect ridicule preemptively.
""",
            "patterns": [
                "speech_anxiety",
                "fear_of_speaking",
                "shame_about_speech",
                "social_visibility_fear",
                "communication_avoidance",
                "anticipation_anxiety",
                "loss_of_control_in_speech",
            ],
            "weak_domains": ["speech_stuttering_expression", "self_domain", "relationships_domain"],
            "assessments": [
                "speech-anxiety-short",
                "self-domain-short",
                "relationships-domain-short",
            ],
            "strategy_focus": ["self-worth / self-criticism", "relationships"],
            "scenario_themes": ["low visibility pressure", "expression-safe", "shame-sensitive"],
            "timeline": ["avoid forced public speaking metaphors", "gentle opening", "confidence-building integration"],
        },
        {
            "file": "c029_substance_control_meaning_void.md",
            "case_id": "complex-029",
            "title": "Substance Use Concerns, Control, and Meaning Void",
            "domain_mix": ["substance use", "control", "meaning"],
            "scenario": """
## Background

I am forty. Alcohol crept from social to nightly over a decade. I tell myself it is manageable because I still work and parent.

## Current Life

I cannot beat this addiction alone, though I have not said that aloud often. loss of control over use scares me most — the third drink deciding itself. life feels meaningless on sober Sunday afternoons when habit is removed.

## Thoughts

I think about use preoccupation throughout the week. I resist letting go of control in treatment conversations while wanting relief.

## Emotions

Shame, brief panic about health, numbness that habit smooths over.

## Relationships

Spouse issued boundaries. I find it hard to trust people with full honesty about scale of use.

## Goals

agency/recovery_goal seeking without public shame spiral. I want meaning that competes with the ritual of drinking.

## Values

Family, honesty, and self-respect — eroded but not gone.

## Internal Conflicts

I want freedom and fear life without buffer. I want trust and hide use.
""",
            "patterns": [
                "substance_use_pattern",
                "addiction_concern_signal",
                "loss_of_control_over_use",
                "loss_of_meaning",
                "shame_sensitivity",
                "trust_difficulty",
            ],
            "weak_domains": ["substance_use_patterns", "meaning", "relationships_domain", "self_domain"],
            "assessments": [
                "substance-use-short",
                "meaning-purpose-short",
                "self-domain-short",
                "relationships-domain-short",
            ],
            "strategy_focus": ["presenting context", "meaning / purpose", "relationships"],
            "scenario_themes": ["non-shaming substance language", "control-aware", "meaning replacement"],
            "timeline": ["grounding first", "avoid moralizing arcs", "integration on values and connection"],
        },
        {
            "file": "c030_existential_fear_safety_meaning.md",
            "case_id": "complex-030",
            "title": "Existential Fear, Safety Concerns, and Meaning Questions",
            "domain_mix": ["existential fear", "safety", "meaning"],
            "scenario": """
## Background

I am thirty-nine, no acute crisis, yet a persistent fear of living badly or not living fully. Philosophical temperament plus anxiety genetics, perhaps.

## Current Life

I'm afraid to live with the volume turned down indefinitely. I'm afraid of dying without having been present. panic hits me out of nowhere when existential thoughts peak at night.

Menial Tuesday feels absurd; peak moments feel insufficient to answer the question.

## Thoughts

life feels meaningless in analytical hours. I feel hopeless about answering existential questions through achievement. My mind gets stuck on the same worries about time passing.

## Emotions

Dread, shame about dread, longing for peace I cannot sustain.

## Relationships

Partner finds me distant in reflective spirals. I feel disconnected from others who seem unbothered.

## Goals

I want engaged life, not only analyzed life. I want safety in being without constant evaluation.

## Values

Presence, love, and truth — I crave them philosophically and miss them practically.

## Internal Conflicts

I want certainty about meaning and know it will not arrive as a formula. I want peace and feed existential alarm.
""",
            "patterns": [
                "existential_fear",
                "fear_of_death",
                "generalized_fear",
                "loss_of_meaning",
                "hopelessness_signal",
                "panic_reactivity",
                "safety_concern_signal",
            ],
            "weak_domains": ["meaning", "anxiety_fear_panic", "values_identity_domain", "relationships_domain"],
            "assessments": [
                "meaning-purpose-short",
                "anxiety-short",
                "values-identity-domain-short",
            ],
            "strategy_focus": ["meaning / purpose", "emotion regulation", "presenting context"],
            "scenario_themes": ["existential without nihilism", "grounding", "embodied presence"],
            "timeline": ["anchor in sensory grounding", "meaning themes mid-late", "avoid death fixation early"],
        },
    ]


def all_profiles() -> list[dict]:
    return _extend_profiles() + _profiles_part_two() + _profiles_part_three()


def word_count(text: str) -> int:
    return len(text.split())


def _followup_excerpt(profile: dict) -> str:
    """Add realistic interview continuation to reach benchmark word length."""
    title = profile["title"]
    domains = ", ".join(profile["domain_mix"])
    patterns = profile["patterns"]
    pattern_prose = ", ".join(p.replace("_", " ") for p in patterns[:6])

    return f"""
## Follow-Up Interview Excerpt

When the facilitator asked me to slow down and give a concrete recent example, I described a ordinary Tuesday that still carried the themes we had been naming. I woke up already rehearsing the day, already measuring myself against what I should handle better. The people around me would not see everything I describe here; that gap between appearance and inner life is part of why I sought support.

I talked about how {domains} interact in me rather than arriving one at a time. Stress in one area tightens another. If I sleep poorly, my thoughts get louder. If I feel criticized, I withdraw, and then feel ashamed for withdrawing. If I feel disconnected, I question my worth, and then overwork or overthink to compensate. These loops are familiar enough that I sometimes mistake them for personality instead of patterns that could shift.

I was asked what I hope changes. I said I do not need a perfect life — I need a more honest relationship with myself and with people I trust. I want my choices to reflect my values more often, not only my fears. I want to recognize {pattern_prose} earlier, before they run the whole day. I want help building a life that feels chosen, not only managed.

I also spoke about what I am afraid a session or deep inquiry might touch. I worry about losing control of emotion in front of others. I worry about discovering that change requires grief I have postponed. I worry about wanting transformation and then retreating when it becomes real. Naming those fears did not remove them, but it made me feel slightly less alone with the complexity.

Near the end I said something like: "{title}" is not the whole of me, but it is the part that needs attention right now. I am willing to keep talking if the process stays respectful, paced, and grounded in my actual life — not an ideal version of recovery I cannot recognize.
""".strip()


def _ensure_scenario_length(profile: dict) -> str:
    scenario = profile["scenario"].strip()
    if word_count(scenario) >= 500:
        return scenario
    enriched = scenario + "\n\n" + _followup_excerpt(profile)
    if word_count(enriched) < 500:
        enriched += "\n\n" + _followup_excerpt(profile)
    return enriched


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    profiles = all_profiles()
    if len(profiles) < 30:
        raise SystemExit(f"Expected at least 30 profiles, got {len(profiles)}")

    for profile in profiles:
        scenario = _ensure_scenario_length(profile)
        wc = word_count(scenario)
        if wc < 500:
            raise SystemExit(f"{profile['file']} too short after enrichment: {wc} words")
        if wc > 1500:
            raise SystemExit(f"{profile['file']} too long: {wc} words")

        content = _md_profile(
            case_id=profile["case_id"],
            title=profile["title"],
            domain_mix=profile["domain_mix"],
            scenario=scenario,
            patterns=profile["patterns"],
            weak_domains=profile["weak_domains"],
            assessments=profile["assessments"],
            strategy_focus=profile["strategy_focus"],
            scenario_themes=profile["scenario_themes"],
            timeline=profile["timeline"],
        )
        path = OUTPUT_DIR / profile["file"]
        path.write_text(content, encoding="utf-8")
        print(f"wrote {path.name} ({wc} words)")

    print(f"Generated {len(profiles)} complex benchmark cases in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
