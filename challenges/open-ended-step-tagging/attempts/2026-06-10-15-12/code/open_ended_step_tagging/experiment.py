import csv
import hashlib
import os
import random
import re
from collections import defaultdict
from pathlib import Path

from dallinger import db
from dominate import tags

import psynet.experiment
from psynet.asset import asset
from psynet.consent import NoConsent
from psynet.modular_page import AudioPrompt, ModularPage, SurveyJSControl
from psynet.page import InfoPage
from psynet.recruiters import get_lucid_settings
from psynet.timeline import Event, Timeline
from psynet.trial.static import StaticNode, StaticTrial, StaticTrialMaker
from psynet.utils import get_translator

_ = get_translator(namespace="experiment")

LANGUAGE = "ENG"
COUNTRY = "US"
USE_CINT_LOCAL_MOCK = os.environ.get("PSYNET_CINT_LOCAL_MOCK") == "1"
REAL_LUCID_CONFIG_PATH = f"qualifications/lucid/lucid-{LANGUAGE}-{COUNTRY}.json"
LOCAL_MOCK_LUCID_CONFIG_PATH = (
    f"qualifications/lucid/mock-lucid-{LANGUAGE}-{COUNTRY}.json"
)
LUCID_CONFIG_PATH = (
    LOCAL_MOCK_LUCID_CONFIG_PATH if USE_CINT_LOCAL_MOCK else REAL_LUCID_CONFIG_PATH
)

recruiter_settings = get_lucid_settings(
    lucid_recruitment_config_path=LUCID_CONFIG_PATH,
    termination_time_in_s=120 * 60,
    debug_recruiter=USE_CINT_LOCAL_MOCK,
    initial_response_within_s=180,
    inactivity_timeout_in_s=15 * 60,
    no_focus_timeout_in_s=10 * 60,
    bid_incidence=66,
)

if USE_CINT_LOCAL_MOCK:
    recruiter_settings = {
        **recruiter_settings,
        "recruiter": "generic",
        "debug_recruiter": "HotAirRecruiter",
        "currency": "$",
    }

STIMULUS_MANIFEST = Path("data/stimuli.csv")
MIN_ITERATIONS_PER_STIMULUS = 5
CLIP_DURATION_SECONDS = 15
SUBMIT_DELAY_SECONDS = CLIP_DURATION_SECONDS
MAX_TAG_CHARS = 15
GENRE_LABELS = {
    "blues",
    "classical",
    "country",
    "folk",
    "hiphop",
    "jazz",
    "metal",
    "pop",
    "rap",
    "reggae",
    "rock",
}


def list_stimuli():
    with STIMULUS_MANIFEST.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def get_nodes():
    return [
        StaticNode(
            definition={
                "stimulus_id": row["stimulus_id"],
                "culture": row["culture"],
                "description": row["description"],
                "audio_path": row["audio_path"],
            },
            block=row["culture"],
            assets={
                "stimulus_audio": asset(
                    row["audio_path"],
                    extension=".wav",
                    cache=True,
                )
            },
        )
        for row in list_stimuli()
    ]


def normalize_tag(tag):
    return tag.strip().lower()


def parse_tag_text(text):
    if not text:
        return []
    raw_tags = re.split(r"[,;\n]+", text)
    seen = set()
    normalized_tags = []
    for raw_tag in raw_tags:
        tag = normalize_tag(raw_tag)
        if tag and tag not in seen:
            seen.add(tag)
            normalized_tags.append(tag)
    return normalized_tags


def invalid_tags(tags_to_check):
    return [
        tag
        for tag in tags_to_check
        if len(tag) > MAX_TAG_CHARS
        or any(character.isspace() for character in tag)
        or tag in GENRE_LABELS
    ]


def tag_field(tag):
    digest = hashlib.sha1(tag.encode("utf-8")).hexdigest()[:10]
    return f"tag_{digest}"


def completed_trials_for_stimulus(stimulus_id, exclude_trial_id=None):
    query = db.session.query(StepTaggingTrial).filter(StepTaggingTrial.complete == True)
    completed = []
    for trial in query.all():
        if exclude_trial_id is not None and trial.id == exclude_trial_id:
            continue
        if trial.definition.get("stimulus_id") == stimulus_id and trial.answer:
            completed.append(trial)
    return sorted(completed, key=lambda trial: trial.id)


def existing_tag_records(stimulus_id, exclude_trial_id=None):
    trials = completed_trials_for_stimulus(stimulus_id, exclude_trial_id)
    tags_by_name = defaultdict(lambda: {"ratings": [], "flags": 0, "sources": 0})

    for trial in trials:
        answer = trial.answer or {}
        for tag in answer.get("new_tags", []):
            tags_by_name[tag]["sources"] += 1
        for tag, rating in answer.get("ratings", {}).items():
            if rating is not None:
                tags_by_name[tag]["ratings"].append(float(rating))
        for tag in answer.get("flags", []):
            tags_by_name[tag]["flags"] += 1

    records = []
    for tag, values in tags_by_name.items():
        average_rating = (
            sum(values["ratings"]) / len(values["ratings"])
            if values["ratings"]
            else None
        )
        records.append(
            {
                "tag": tag,
                "field": tag_field(tag),
                "source_count": values["sources"],
                "average_rating": average_rating,
                "flag_count": values["flags"],
            }
        )

    return sorted(
        records,
        key=lambda record: (
            -(record["average_rating"] or 0),
            -record["source_count"],
            record["tag"],
        ),
    )


def validate_tagging_answer(answer, existing_tags):
    entered_tags = parse_tag_text(answer.get("new_tags", ""))
    bad_tags = invalid_tags(entered_tags)

    if bad_tags:
        return _(
            "Please keep tags as single emotion words, no more than {MAX_CHARS} characters, and not genre labels. Check: {TAGS}."
        ).format(MAX_CHARS=MAX_TAG_CHARS, TAGS=", ".join(bad_tags))

    if not existing_tags and not entered_tags:
        return _("Please enter at least one emotion tag before continuing.")

    return None


def survey_design(existing_tags):
    elements = [
        {
            "type": "comment",
            "name": "new_tags",
            "title": _("Add any new emotion or affect tags for this clip."),
            "description": _(
                "Use single words in your native language. Separate multiple tags with commas or new lines. Do not use genre labels or lyrics."
            ),
            "placeholder": _("for example: joyful, tense, lonely"),
            "rows": 3,
        }
    ]

    for record in existing_tags:
        elements.append(
            {
                "type": "rating",
                "name": f"rating_{record['field']}",
                "title": _('How well does "{TAG}" describe the clip?').format(
                    TAG=record["tag"]
                ),
                "isRequired": False,
                "rateMin": 1,
                "rateMax": 5,
                "minRateDescription": _("Does not apply"),
                "maxRateDescription": _("Applies very well"),
            }
        )

    if existing_tags:
        elements.append(
            {
                "type": "checkbox",
                "name": "flagged_tags",
                "title": _("Flag any existing tags that should be reviewed."),
                "description": _(
                    "Flag tags that are inappropriate, irrelevant, misspelled beyond recognition, genre labels, direct lyrics, or not emotion words."
                ),
                "choices": [
                    {"value": record["field"], "text": record["tag"]}
                    for record in existing_tags
                ],
            }
        )

    return {"elements": elements, "showQuestionNumbers": "false"}


def make_bot_response(existing_tags):
    seed_tags = ["joyful", "tense", "calm", "sad", "bright", "lonely"]
    answer = {"new_tags": ", ".join(random.sample(seed_tags, 2))}
    for record in existing_tags:
        answer[f"rating_{record['field']}"] = random.randint(2, 5)
    answer["flagged_tags"] = []
    return answer


class StepTaggingTrial(StaticTrial):
    time_estimate = 45

    def show_trial(self, experiment, participant):
        records = existing_tag_records(self.definition["stimulus_id"], self.id)
        prompt_text = _(
            "Listen to the whole clip. Then add new emotion tags and rate any tags from earlier participants."
        )
        return ModularPage(
            "step_tagging",
            AudioPrompt(
                self.assets["stimulus_audio"],
                prompt_text,
                controls=["Play"],
            ),
            SurveyJSControl(
                survey_design(records),
                show_question_numbers=False,
                bot_response=lambda: make_bot_response(records),
            ),
            validate=lambda answer: validate_tagging_answer(answer, records),
            events={
                "submitEnable": Event(
                    is_triggered_by="trialConstruct", delay=SUBMIT_DELAY_SECONDS
                )
            },
            time_estimate=self.time_estimate,
        )

    def format_answer(self, raw_answer, **kwargs):
        answer = raw_answer or {}
        records = existing_tag_records(self.definition["stimulus_id"], self.id)
        field_to_tag = {record["field"]: record["tag"] for record in records}
        entered_tags = parse_tag_text(answer.get("new_tags", ""))
        ratings = {
            field_to_tag[field]: answer.get(f"rating_{field}")
            for field in field_to_tag
            if answer.get(f"rating_{field}") is not None
        }
        flagged_fields = answer.get("flagged_tags") or []
        return {
            "stimulus_id": self.definition["stimulus_id"],
            "culture": self.definition["culture"],
            "iteration": len(
                completed_trials_for_stimulus(self.definition["stimulus_id"], self.id)
            )
            + 1,
            "new_tags": entered_tags,
            "ratings": ratings,
            "flags": [field_to_tag[field] for field in flagged_fields if field in field_to_tag],
            "existing_tags_seen": records,
        }


class Exp(psynet.experiment.Experiment):
    label = "Open-ended STEP tagging"

    config = {
        "recruiter": "lucid",
        "locale": "en",
        "supported_locales": ["en"],
        **recruiter_settings,
        "wage_per_hour": 12.0,
        "publish_experiment": True,
    }

    timeline = Timeline(
        NoConsent(),
        InfoPage(
            tags.div(
                tags.h2(_("Open-ended music emotion tagging")),
                tags.p(
                    _(
                        "In this study you will listen to short music clips and describe the emotions or affective qualities you hear."
                    )
                ),
                tags.ul(
                    tags.li(_("Use single-word tags in your native language.")),
                    tags.li(
                        _(
                            "Do not enter genre labels, direct lyrics, or tags longer than 15 characters."
                        )
                    ),
                    tags.li(
                        _(
                            "When previous participants have suggested tags, rate how well they fit and flag tags that should be reviewed."
                        )
                    ),
                ),
            ),
            time_estimate=10,
        ),
        StaticTrialMaker(
            id_="step_tagging",
            trial_class=StepTaggingTrial,
            nodes=get_nodes,
            expected_trials_per_participant="n_nodes",
            max_trials_per_participant="n_nodes",
            target_trials_per_node=MIN_ITERATIONS_PER_STIMULUS,
            recruit_mode="n_trials",
            balance_across_nodes=True,
            check_performance_at_end=False,
            check_performance_every_trial=False,
        ),
        InfoPage(
            _("Thank you. Your tags will help build a weighted emotion vocabulary for each clip."),
            time_estimate=5,
        ),
    )

    def test_experiment(self):
        super().test_experiment()
        completed = db.session.query(StepTaggingTrial).filter(
            StepTaggingTrial.complete == True
        )
        answers = [trial.answer for trial in completed.all() if trial.answer]
        assert answers, "Expected bot trials to save STEP tagging answers."
        for answer in answers:
            assert "stimulus_id" in answer
            assert "new_tags" in answer
            assert "ratings" in answer
            assert "flags" in answer


if __name__ == "__main__":
    stimuli = list_stimuli()
    print(f"Found {len(stimuli)} demo stimuli:")
    for stimulus in stimuli:
        print(
            f"- {stimulus['stimulus_id']} ({stimulus['culture']}): {stimulus['audio_path']}"
        )
