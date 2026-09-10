"""Open-ended STEP tagging experiment for cross-cultural music emotion tags."""

from __future__ import annotations

import csv
import html
import os
from collections import defaultdict
from copy import deepcopy
from pathlib import Path

import psynet.experiment
from dominate import tags
from markupsafe import Markup
from psynet.asset import asset
from psynet.page import InfoPage, VolumeCalibration
from psynet.timeline import Timeline
from psynet.trial.main import TrialNetwork
from psynet.utils import get_translator
from step import StepTag

_ = get_translator(namespace="experiment")

MANIFEST_PATH = Path("data/stimuli.csv")
TARGET_CULTURE = os.environ.get("TARGET_CULTURE", "US")
CLIPS_PER_PARTICIPANT = 15
MAX_ITERATIONS_PER_CLIP = 5
MAX_TAG_LENGTH = 15
GENRE_LABELS = {
    "ballad",
    "blues",
    "country",
    "funk",
    "hiphop",
    "jazz",
    "kpop",
    "pop",
    "rap",
    "rock",
    "samba",
}


def load_manifest(path: Path = MANIFEST_PATH) -> list[dict[str, str]]:
    """Load replaceable stimulus metadata from CSV."""

    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    required = {"clip_id", "culture", "audio_path", "description"}
    missing = required.difference(rows[0].keys() if rows else [])
    if missing:
        raise ValueError(f"Stimulus manifest is missing columns: {sorted(missing)}")

    for row in rows:
        audio_path = Path(row["audio_path"])
        if not audio_path.exists():
            raise FileNotFoundError(f"Missing audio stimulus: {audio_path}")

    return rows


def select_balanced_rows(
    rows: list[dict[str, str]],
    target_culture: str = TARGET_CULTURE,
    max_clips: int = CLIPS_PER_PARTICIPANT,
) -> list[dict[str, str]]:
    """Select a deterministic culture-balanced subset for the active country."""

    by_culture: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_culture[row["culture"]].append(row)

    cultures = sorted(by_culture)
    if len(cultures) < 3:
        raise ValueError("The STEP tagging demo requires at least three culture labels.")

    if len(rows) <= max_clips:
        return sorted(rows, key=lambda row: (row["culture"] != target_culture, row["culture"], row["clip_id"]))

    own_quota = max(1, max_clips // 2)
    other_cultures = [culture for culture in cultures if culture != target_culture]
    other_quota = max(1, (max_clips - own_quota) // max(1, len(other_cultures)))

    selected = by_culture.get(target_culture, [])[:own_quota]
    for culture in other_cultures:
        selected.extend(by_culture[culture][:other_quota])

    remaining = [row for row in rows if row not in selected]
    selected.extend(remaining[: max_clips - len(selected)])
    return selected[:max_clips]


def list_stimuli() -> dict[str, object]:
    """Return STEP stimuli keyed by clip id."""

    return {
        row["clip_id"]: asset(Path(row["audio_path"]), extension=".wav", cache=True)
        for row in select_balanced_rows(load_manifest())
    }


def normalize_tag(tag: str) -> str:
    return html.unescape(tag).strip().strip(".,;:!?\"'").lower()


def is_valid_tag(tag: str) -> bool:
    """Validate a native-language single-word tag without rejecting accents or Hangul."""

    tag = normalize_tag(tag)
    return (
        bool(tag)
        and len(tag) <= MAX_TAG_LENGTH
        and not any(character.isspace() for character in tag)
        and any(character.isalnum() for character in tag)
        and tag not in GENRE_LABELS
    )


class EmotionAudioStepTag(StepTag):
    """STEP-Tag variant with music-emotion instructions and tag validation."""

    @classmethod
    def get_jinja_translations(cls):
        instructions_without_tags = Markup(
            str(
                tags.div(
                    tags.h3(_("Describe the emotion in this music")),
                    tags.div(
                        tags.p(
                            _(
                                "Nobody has added tags for this clip yet. Add one or more native-language emotion or affect words that describe what the music expresses."
                            )
                        ),
                        tags.p(
                            _(
                                "Press Enter after each tag. Tags must be single words, no longer than 15 characters, and must not be genre labels or lyrics."
                            )
                        ),
                        cls="alert alert-primary",
                        role="alert",
                    ),
                ),
            )
        )
        instructions_with_tags = Markup(
            str(
                tags.div(
                    tags.h3(_("Rate and refine the current tags")),
                    tags.div(
                        tags.p(
                            _(
                                "First rate every visible tag for how well it describes the clip."
                            )
                        ),
                        tags.p(
                            _(
                                "Click the flag icon for typos, irrelevant terms, genre labels, copied lyrics, or non-emotion descriptors."
                            )
                        ),
                        tags.p(
                            _(
                                "Then add any missing single-word emotion tags in your native language."
                            )
                        ),
                        cls="alert alert-primary",
                        role="alert",
                    ),
                ),
            )
        )
        return {
            "title_frozen": _("Completed tags"),
            "title_unfrozen": _("Rate existing tags"),
            "type_more": _("Type more tags"),
            "title_tags": _("Add emotion tags"),
            "next": _("Next"),
            "instructions_without_tags": instructions_without_tags,
            "instructions_with_tags": instructions_with_tags,
        }

    @classmethod
    def get_javascript_translations(cls):
        return {
            "translations": {
                "rate_all_tags": _("Please rate or flag every visible tag."),
                "specify_one_tag": _("Please add at least one emotion tag."),
                "cannot_submit": _("Please submit or delete the text still in the tag field."),
                "whitespaces": _("Tags should be single words; remove spaces before submitting."),
            }
        }

    def format_answer(self, trial, raw_answer):
        answer = deepcopy(raw_answer)
        accepted_tags = []
        rejected_tags = []

        for tag in answer.get("new_tags", []):
            normalized = normalize_tag(tag)
            if is_valid_tag(normalized):
                accepted_tags.append(normalized)
            else:
                rejected_tags.append(tag)

        trial.var.set("accepted_new_tags", accepted_tags)
        trial.var.set("rejected_new_tags", rejected_tags)
        answer["new_tags"] = accepted_tags
        return super().format_answer(trial, answer)


def introduction():
    return InfoPage(
        Markup(
            str(
                tags.div(
                    tags.h3(_("Open-ended music emotion tagging")),
                    tags.p(
                        _(
                            "You will hear short 15-second music clips. For each clip, describe the emotions or affective qualities that the music expresses."
                        )
                    ),
                    tags.ul(
                        tags.li(_("Use single-word tags in your native language.")),
                        tags.li(_("Do not enter genre labels, artist names, or lyrics.")),
                        tags.li(
                            _(
                                "Flag existing tags that are typos, irrelevant, lyrics, genre labels, or not valid emotion descriptors."
                            )
                        ),
                    ),
                ),
            )
        ),
        time_estimate=15,
    )


class Exp(psynet.experiment.Experiment):
    label = "Open-ended STEP tagging"
    test_n_bots = 8

    timeline = Timeline(
        VolumeCalibration(),
        introduction(),
        EmotionAudioStepTag(
            label="emotion_step_tag",
            stimuli=list_stimuli,
            expected_trials_per_participant="n_stimuli",
            max_trials_per_participant="n_stimuli",
            max_iterations=MAX_ITERATIONS_PER_CLIP,
            view_time_estimate=15,
            rating_time_estimate=4,
            creating_time_estimate=8,
            freeze_on_n_ratings=MAX_ITERATIONS_PER_CLIP,
            freeze_on_mean_rating=5,
            complete_on_n_frozen="n_stimuli",
            flagging_threshold=1,
            show_instructions=False,
        ),
        InfoPage(
            _("Thank you. Your tags, ratings, and flags have been saved for review."),
            time_estimate=5,
        ),
    )

    def test_experiment(self):
        super().test_experiment()

        selected_rows = select_balanced_rows(load_manifest())
        cultures = {row["culture"] for row in selected_rows}
        assert len(cultures) >= 3
        assert TrialNetwork.query.count() == len(selected_rows)

        trials = [
            trial
            for trial in self.timeline.trial_makers["emotion_step_tag"].trial_class.query.all()
            if trial.answer is not None
        ]
        assert trials
        assert any(candidate.previous_ratings for trial in trials for candidate in trial.answer.candidates)
        assert any(
            0 in candidate.previous_ratings
            for trial in trials
            for candidate in trial.answer.candidates
        )
