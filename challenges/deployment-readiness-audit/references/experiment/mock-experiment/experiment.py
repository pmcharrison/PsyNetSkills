"""Mock PsyNet experiment for deployment-readiness auditing.

This file is intentionally minimal; the challenge is to audit the surrounding
deployment dossier rather than implement a working experiment.
"""

import psynet.experiment
from psynet.page import InfoPage
from psynet.timeline import Timeline


class Exp(psynet.experiment.Experiment):
    label = "old-beat-validation-template"
    timeline = Timeline(
        InfoPage("Welcome to the copied experiment.", time_estimate=5),
        InfoPage("Thank you.", time_estimate=5),
    )
    config = {
        "title": "Old Beat Validation Template",
        "recruiter": "prolific",
        "base_payment": 1.00,
        "prolific_estimated_completion_minutes": 5,
        "dashboard_user": "cap",
        "dashboard_password": "TODO_REPLACE_BEFORE_DEPLOY",
    }

