#!/usr/bin/env python3
"""Deterministic NIROS profile-to-session pipeline demo."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TextIO

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from niros.human_profile_summary import build_human_profile_summary
from niros.models import SupportedLanguage
from niros.patterns import PatternTag
from niros.scenario_blueprint import build_scenario_blueprint
from niros.scenario_script_skeleton import build_scenario_script_skeleton
from niros.session_simulation import simulate_session
from niros.session_timeline_renderer import render_session_timeline

DEMO_SESSION_ID = "session-demo-001"

SAMPLE_EVIDENCE = {
    "attachment_anxiety": "I feel anxious when people become distant or slow to reply.",
    "emotional_suppression": "I push my feelings down so I can keep going.",
    "rumination": "My mind gets stuck on the same worries and I replay them at night.",
}


def build_sample_profile() -> dict:
    tags = [
        _pattern_tag(
            canonical_id,
            tag_id=f"tag-{index + 1}",
            sequence=index,
            matched_text=matched_text,
        )
        for index, (canonical_id, matched_text) in enumerate(SAMPLE_EVIDENCE.items())
    ]
    return build_human_profile_summary(tags)


def run_session_demo(output_stream: TextIO | None = None) -> int:
    stream = output_stream or sys.stdout

    profile = build_sample_profile()
    blueprint = build_scenario_blueprint(profile)
    skeleton = build_scenario_script_skeleton(blueprint)
    timeline = simulate_session(profile)
    rendered_timeline = render_session_timeline(timeline)

    print("=== NIROS Session Demo ===", file=stream)
    print("", file=stream)
    print("Human Profile", file=stream)
    primary = profile.get("primary_pattern")
    if primary is not None:
        print(
            f"- Primary pattern: {primary['name']} ({primary['count']} references)",
            file=stream,
        )
    secondary = profile.get("secondary_patterns", [])
    if secondary:
        secondary_names = ", ".join(pattern["name"] for pattern in secondary)
        print(f"- Secondary patterns: {secondary_names}", file=stream)
    print(f"- Profile summary: {profile['profile_text']}", file=stream)
    print("", file=stream)

    print("Scenario Blueprint", file=stream)
    print(f"- Opening objective: {blueprint.opening_phase.objective}", file=stream)
    print(f"- Exploration phases: {len(blueprint.exploration_phases)}", file=stream)
    print(f"- Integration objective: {blueprint.integration_phase.objective}", file=stream)
    print("", file=stream)

    print("Scenario Script Skeleton", file=stream)
    print(f"- Title: {skeleton.title}", file=stream)
    print(f"- Segments: {len(skeleton.segments)}", file=stream)
    print(f"- Total estimated duration: {skeleton.total_estimated_duration} min", file=stream)
    print("", file=stream)

    print(rendered_timeline, file=stream)

    return 0


def _pattern_tag(
    canonical_id: str,
    *,
    tag_id: str,
    sequence: int,
    matched_text: str,
) -> PatternTag:
    return PatternTag(
        id=tag_id,
        session_id=DEMO_SESSION_ID,
        evidence_id=f"{DEMO_SESSION_ID}:evidence:{sequence}",
        canonical_id=canonical_id,
        matched_text=matched_text,
        confidence=1.0,
        language=SupportedLanguage.ENGLISH,
    )


def main() -> int:
    return run_session_demo()


if __name__ == "__main__":
    raise SystemExit(main())
