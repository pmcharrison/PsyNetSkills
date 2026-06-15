"""Shared stimulus and profile definitions for the replication-memory study."""

CHOICE_ROLES = ("target", "semantic_lure", "recent_lure", "neutral_lure")

WORD_PAIRS = [
    {
        "pair_id": "L01",
        "condition": "literal",
        "cue": "orchard",
        "target": "apple",
        "semantic_lure": "pear",
        "recent_lure": "window",
        "neutral_lure": "hammer",
        "difficulty": 1,
    },
    {
        "pair_id": "L02",
        "condition": "literal",
        "cue": "harbor",
        "target": "anchor",
        "semantic_lure": "sail",
        "recent_lure": "apple",
        "neutral_lure": "velvet",
        "difficulty": 1,
    },
    {
        "pair_id": "L03",
        "condition": "literal",
        "cue": "library",
        "target": "book",
        "semantic_lure": "paper",
        "recent_lure": "anchor",
        "neutral_lure": "cactus",
        "difficulty": 1,
    },
    {
        "pair_id": "L04",
        "condition": "literal",
        "cue": "kitchen",
        "target": "spoon",
        "semantic_lure": "fork",
        "recent_lure": "book",
        "neutral_lure": "planet",
        "difficulty": 1,
    },
    {
        "pair_id": "I01",
        "condition": "interference",
        "cue": "garden",
        "target": "window",
        "semantic_lure": "flower",
        "recent_lure": "spoon",
        "neutral_lure": "violin",
        "difficulty": 3,
    },
    {
        "pair_id": "I02",
        "condition": "interference",
        "cue": "school",
        "target": "pencil",
        "semantic_lure": "teacher",
        "recent_lure": "window",
        "neutral_lure": "river",
        "difficulty": 3,
    },
    {
        "pair_id": "I03",
        "condition": "interference",
        "cue": "desert",
        "target": "cactus",
        "semantic_lure": "sand",
        "recent_lure": "pencil",
        "neutral_lure": "pillow",
        "difficulty": 3,
    },
    {
        "pair_id": "I04",
        "condition": "interference",
        "cue": "market",
        "target": "basket",
        "semantic_lure": "coin",
        "recent_lure": "cactus",
        "neutral_lure": "cloud",
        "difficulty": 3,
    },
]

PROFILE_DESCRIPTIONS = {
    "psynet_bot_rule": "Rule-following PsyNet bot profile that selects the target answer.",
    "scripted_noisy": "Scripted inattentive profile with stochastic guesses and long response times.",
    "mock_llm_memory_limited": "Prompt-style mock LLM profile with limited ordered memory.",
    "semantic_bias": "Scripted profile that overweights semantically related alternatives.",
}


def choices_for_trial(trial):
    """Return answer choices in stable order for PsyNet and exported simulations."""
    return [trial[role] for role in CHOICE_ROLES]


def role_for_answer(trial, answer):
    for role in CHOICE_ROLES:
        if trial[role] == answer:
            return role
    return "unknown"
