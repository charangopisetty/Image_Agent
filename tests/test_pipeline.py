"""Air-gapped caption pipeline tests — crews are mocked; no live OpenAI calls."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import pytest
from crewai import TaskOutput

from image_agent.cliches import find_banned_phrases
from image_agent.crew import validate_draft
from image_agent.service import format_blind_drafts, load_angles, run_air_gapped_drafters


def _output(raw: str) -> TaskOutput:
    return TaskOutput(description="draft", raw=raw, agent="drafter")


class TestDraftGuardrail:
    def test_accepts_specific_draft(self):
        ok, _ = validate_draft(_output('{"instagram": "Leopard spots on the crust.", "facebook": "Friday pie?"}'))
        assert ok

    def test_rejects_stock_phrases(self):
        ok, feedback = validate_draft(_output('{"instagram": "A mouthwatering pie!", "facebook": "Who’s hungry?"}'))
        assert not ok
        assert "mouthwatering" in feedback
        assert "who's hungry" in feedback

    def test_rejects_talking_about_the_photo(self):
        ok, feedback = validate_draft(_output('{"instagram": "Our kind of close-up.", "facebook": "The plate fills the frame."}'))
        assert not ok
        assert "close-up" in feedback and "the frame" in feedback

    def test_rejects_missing_platform(self):
        ok, feedback = validate_draft(_output('{"instagram": "Leopard spots on the crust."}'))
        assert not ok
        assert "facebook" in feedback

    def test_banned_phrase_matches_whole_words_only(self):
        assert find_banned_phrases("indulgent") == []


class TestBlindDrafts:
    def test_labels_hide_angles(self):
        drafts = [
            {"angle": "close_up", "instagram": "one", "facebook": "1"},
            {"angle": "one_liner", "instagram": "two", "facebook": "2"},
        ]
        blind = format_blind_drafts(drafts, "instagram")
        assert "Draft A:" in blind and "Draft B:" in blind
        assert "close_up" not in blind and "one_liner" not in blind
        assert "1" not in blind


class TestAirGappedDrafters:
    def _fake_crew(self, outcomes: dict[str, str | Exception], seen_inputs: list[dict]):
        def kickoff(inputs):
            seen_inputs.append(inputs)
            outcome = outcomes[inputs["angle_name"]]
            if isinstance(outcome, Exception):
                raise outcome
            return SimpleNamespace(raw=outcome)

        crew = SimpleNamespace(kickoff=kickoff)
        return SimpleNamespace(draft_crew=lambda: crew)

    def test_each_drafter_sees_only_its_own_angle(self):
        angles = load_angles()
        outcomes = {
            angle["name"]: f'{{"instagram": "{angle_id} ig", "facebook": "{angle_id} fb"}}'
            for angle_id, angle in angles.items()
        }
        seen: list[dict] = []
        with patch("image_agent.service.ImageAgent", lambda: self._fake_crew(outcomes, seen)):
            drafts = run_air_gapped_drafters({"creative_brief": "brief"})

        assert {draft["angle"] for draft in drafts} == set(angles)
        assert sorted(inputs["lead_hook"] for inputs in seen) == list(range(1, len(angles) + 1))
        for inputs in seen:
            assert "instagram_drafts" not in inputs
            assert "facebook_drafts" not in inputs

    def test_continues_when_one_drafter_fails(self):
        angles = load_angles()
        names = [angle["name"] for angle in angles.values()]
        outcomes = {name: '{"instagram": "ig", "facebook": "fb"}' for name in names}
        outcomes[names[0]] = RuntimeError("boom")
        with patch("image_agent.service.ImageAgent", lambda: self._fake_crew(outcomes, [])):
            drafts = run_air_gapped_drafters({"creative_brief": "brief"})
        assert len(drafts) == len(names) - 1

    def test_raises_when_every_drafter_fails(self):
        outcomes = {angle["name"]: RuntimeError("boom") for angle in load_angles().values()}
        with patch("image_agent.service.ImageAgent", lambda: self._fake_crew(outcomes, [])):
            with pytest.raises(RuntimeError, match="All caption drafters failed"):
                run_air_gapped_drafters({"creative_brief": "brief"})
