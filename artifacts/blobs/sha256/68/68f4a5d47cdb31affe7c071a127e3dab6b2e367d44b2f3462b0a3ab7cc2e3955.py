from __future__ import annotations

import math

from psynet.modular_page import RatingScale

PANAS_MIN_DESCRIPTION = "Very slightly or not at all"
PANAS_MAX_DESCRIPTION = "Extremely"

PANAS_ITEMS = [
    ("interested", "Interested", "Positive affect item used to approximate the abbreviated PANAS described in the paper."),
    ("excited", "Excited", "Positive affect item used to approximate the abbreviated PANAS described in the paper."),
    ("enthusiastic", "Enthusiastic", "Positive affect item used to approximate the abbreviated PANAS described in the paper."),
    ("inspired", "Inspired", "Positive affect item used to approximate the abbreviated PANAS described in the paper."),
    ("determined", "Determined", "Positive affect item used to approximate the abbreviated PANAS described in the paper."),
    ("distressed", "Distressed", "Negative affect item used to approximate the abbreviated PANAS described in the paper."),
    ("upset", "Upset", "Negative affect item used to approximate the abbreviated PANAS described in the paper."),
    ("scared", "Scared", "Negative affect item used to approximate the abbreviated PANAS described in the paper."),
    ("nervous", "Nervous", "Negative affect item used to approximate the abbreviated PANAS described in the paper."),
    ("jittery", "Jittery", "Negative affect item used to approximate the abbreviated PANAS described in the paper."),
]

EMOTION_DIMENSIONS = [
    {
        "name": "valence",
        "title": "Valence",
        "description": "Is the chord conveying positive or negative feelings?",
        "min_description": "Negative",
        "max_description": "Positive",
    },
    {
        "name": "tension",
        "title": "Tension",
        "description": "How tense do you think the chord is? Is it calm and relaxed or tense and agitated?",
        "min_description": "Relaxed",
        "max_description": "Tense",
    },
    {
        "name": "energy",
        "title": "Energy",
        "description": "Do you think the chord is strong and energetic or weak and feeble?",
        "min_description": "Low",
        "max_description": "High",
    },
    {
        "name": "nostalgia_longing",
        "title": "Nostalgia/longing",
        "description": "Is the chord conveying feelings of nostalgia, wistfulness, or longing?",
        "min_description": "Very slightly or not at all",
        "max_description": "Extremely",
    },
    {
        "name": "melancholy_sadness",
        "title": "Melancholy/sadness",
        "description": "How much melancholy or sadness does the chord express?",
        "min_description": "Very slightly or not at all",
        "max_description": "Extremely",
    },
    {
        "name": "interest_expectancy",
        "title": "Interest/expectancy",
        "description": "Is the chord sounding resolutive and definitive or is it conveying feelings of interest and expectancy?",
        "min_description": "Very slightly or not at all",
        "max_description": "Extremely",
    },
    {
        "name": "happiness_joy",
        "title": "Happiness/joy",
        "description": "How much happiness or joy does the chord express?",
        "min_description": "Very slightly or not at all",
        "max_description": "Extremely",
    },
    {
        "name": "tenderness",
        "title": "Tenderness",
        "description": "Is the chord sounding tender and affectionate?",
        "min_description": "Very slightly or not at all",
        "max_description": "Extremely",
    },
    {
        "name": "liking_preference",
        "title": "Liking/preference",
        "description": "How much did you like the chord? This is a purely subjective rating.",
        "min_description": "Very slightly or not at all",
        "max_description": "Extremely",
    },
]

OMSI_PRACTICE_CATEGORIES = [
    "rarely_or_never",
    "one_hour_per_month",
    "one_hour_per_week",
    "fifteen_minutes_per_day",
    "one_hour_per_day",
    "more_than_two_hours_per_day",
]
OMSI_PRACTICE_LABELS = [
    "I rarely or never practice singing or playing an instrument",
    "About 1 hour per month",
    "About 1 hour per week",
    "About 15 minutes per day",
    "About 1 hour per day",
    "More than 2 hours per day",
]
OMSI_PRACTICE_LOGIT = {
    "rarely_or_never": 0.0,
    "one_hour_per_month": 0.060,
    "one_hour_per_week": 0.098,
    "fifteen_minutes_per_day": 0.301,
    "one_hour_per_day": 1.211,
    "more_than_two_hours_per_day": 1.528,
}

OMSI_COURSEWORK_CATEGORIES = [
    "none",
    "one_or_two_nonmajor_courses",
    "three_or_more_nonmajor_courses",
    "preparatory_program",
    "one_year_bmus",
    "two_years_bmus",
    "three_or_more_years_bmus",
    "bmus_degree",
    "graduate_level",
]
OMSI_COURSEWORK_LABELS = [
    "None",
    "1 or 2 non-major courses",
    "3 or more courses for non-majors",
    "An introductory or preparatory music program for Bachelor's level work",
    "1 year of full-time coursework in a Bachelor of Music degree program (or equivalent)",
    "2 years of full-time coursework in a Bachelor of Music degree program (or equivalent)",
    "3 or more years of full-time coursework in a Bachelor of Music degree program (or equivalent)",
    "Completion of a Bachelor of Music degree program (or equivalent)",
    "One or more graduate-level music courses or degrees",
]
OMSI_COURSEWORK_LOGIT = {
    "none": -0.423,
    "one_or_two_nonmajor_courses": 0.274,
    "three_or_more_nonmajor_courses": 0.616,
    "preparatory_program": 0.443,
    "one_year_bmus": 0.055,
    "two_years_bmus": 0.801,
    "three_or_more_years_bmus": 1.387,
    "bmus_degree": 1.390,
    "graduate_level": 3.050,
}

OMSI_COMPOSITION_CATEGORIES = [
    "never",
    "bits_and_pieces",
    "completed_but_not_performed",
    "performed_in_educational_context",
    "performed_for_local_audience",
    "performed_for_regional_or_national_audience",
]
OMSI_COMPOSITION_LABELS = [
    "Have never composed any music",
    "Have composed bits and pieces, but have never completed a piece of music",
    "Have composed one or more complete pieces, but none have been performed",
    "Have composed pieces as assignments or projects for music classes, and one or more of them have been performed or recorded there",
    "Have composed pieces that have been performed for a local audience",
    "Have composed pieces that have been performed for a regional or national audience",
]
OMSI_COMPOSITION_LOGIT = {
    "never": 0.0,
    "bits_and_pieces": 0.516,
    "completed_but_not_performed": 1.071,
    "performed_in_educational_context": 0.875,
    "performed_for_local_audience": 0.456,
    "performed_for_regional_or_national_audience": 1.187,
}

OMSI_CONCERT_CATEGORIES = [
    "none",
    "one_to_four",
    "five_to_eight",
    "nine_to_twelve",
    "thirteen_or_more",
]
OMSI_CONCERT_LABELS = [
    "None",
    "1-4",
    "5-8",
    "9-12",
    "13 or more",
]
OMSI_CONCERT_LOGIT = {
    "none": 0.0,
    "one_to_four": 1.839,
    "five_to_eight": 1.394,
    "nine_to_twelve": 1.713,
    "thirteen_or_more": 1.610,
}

OMSI_TITLE_CATEGORIES = [
    "nonmusician",
    "music_loving_nonmusician",
    "amateur_musician",
    "serious_amateur_musician",
    "semiprofessional_musician",
    "professional_musician",
]
OMSI_TITLE_LABELS = [
    "Nonmusician",
    "Music-loving nonmusician",
    "Amateur musician",
    "Serious amateur musician",
    "Semiprofessional musician",
    "Professional musician",
]
OMSI_TITLE_LOGIT = {
    "nonmusician": 0.0,
    "music_loving_nonmusician": -0.553,
    "amateur_musician": 0.328,
    "serious_amateur_musician": 1.589,
    "semiprofessional_musician": 1.460,
    "professional_musician": 2.940,
}


def panas_scales():
    return [
        RatingScale(
            name=name,
            values=5,
            title=title,
            description=description,
            min_description=PANAS_MIN_DESCRIPTION,
            max_description=PANAS_MAX_DESCRIPTION,
        )
        for name, title, description in PANAS_ITEMS
    ]


def emotion_scales():
    return [
        RatingScale(
            name=dimension["name"],
            values=5,
            title=dimension["title"],
            description=dimension["description"],
            min_description=dimension["min_description"],
            max_description=dimension["max_description"],
        )
        for dimension in EMOTION_DIMENSIONS
    ]


def scale_names():
    return [dimension["name"] for dimension in EMOTION_DIMENSIONS]


def score_omsi(answers: dict[str, str | int | float]):
    age = int(answers["omsi_age"])
    age_started = int(answers["omsi_age_started"])
    if age_started == 0:
        age_started = age

    logit = -3.513
    logit += 0.027 * age
    logit += -0.026 * age_started
    logit += 0.076 * int(answers["omsi_private_lessons_years"])
    logit += 0.042 * int(answers["omsi_regular_practice_years"])
    logit += OMSI_PRACTICE_LOGIT[answers["omsi_current_practice_amount"]]
    logit += OMSI_COURSEWORK_LOGIT[answers["omsi_college_coursework"]]
    logit += OMSI_COMPOSITION_LOGIT[answers["omsi_composition_experience"]]
    logit += OMSI_CONCERT_LOGIT[answers["omsi_concert_attendance"]]
    logit += OMSI_TITLE_LOGIT[answers["omsi_self_title"]]

    probability = 1.0 / (1.0 + math.exp(-logit))
    score = int(round(probability * 1000))
    if score < 250:
        group = "lower_non_musician"
    elif score < 500:
        group = "higher_non_musician"
    elif score < 750:
        group = "lower_musician"
    else:
        group = "higher_musician"

    return {
        "logit": round(logit, 6),
        "probability": round(probability, 6),
        "score": score,
        "group": group,
    }
