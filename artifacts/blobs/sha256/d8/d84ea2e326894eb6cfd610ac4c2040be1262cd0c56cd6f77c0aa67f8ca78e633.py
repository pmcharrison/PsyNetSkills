import time
from typing import Optional

from psynet.modular_page import Control, ModularPage, Prompt

from .game_parameters import BOT_TIMEOUT_STAGE, ENDOWMENT, RNG


def _timeout_answer(stage, answer):
    return 'No answer' if BOT_TIMEOUT_STAGE == stage else answer


def page_start_key(participant, label):
    return f'ultimatum_page_start__{participant.id}__{label}'


def persistent_start(participant, label, fallback=None):
    key = page_start_key(participant, label)
    if participant.var.has(key):
        return getattr(participant.var, key)
    value = fallback if fallback is not None else time.time()
    participant.var.set(key, value)
    return value


class TimedModularPage(ModularPage):
    def timer_persist_label(self):
        return f'{self.label}_{self.prompt.round}'

    def render(self, experiment, participant):
        if isinstance(self.prompt, TimeoutPrompt):
            label = self.timer_persist_label()
            start = persistent_start(participant, label, self.prompt.currentTime)
            self.prompt.currentTime = start
            self.prompt.timerStorageKey = page_start_key(participant, label)
        return super().render(experiment, participant)


class TimeoutPrompt(Prompt):
    macro = 'timeout'
    external_template = 'custom-prompt-with-timer.html'

    def __init__(self, round_, timeout, text='', timeout_answer='No answer', num_rounds=1, show_rounds=True):
        super().__init__(text=text)
        self.round = round_
        self.timeoutSeconds = timeout
        self.timeoutAnswer = timeout_answer
        self.num_rounds = num_rounds
        self.show_rounds = show_rounds
        self.currentTime = None
        self.timerStorageKey = None


class UltimatumControl(Control):
    macro = 'ultimatum'
    external_template = 'ultimatum-control.html'

    def __init__(self, phase, accumulated_score_me=0, accumulated_score_partner=0, proposal=None, round_payoff=0, feedback='', round_failed=False):
        super().__init__()
        self.phase = phase
        self.start_value = ENDOWMENT // 2
        self.min_value = 0
        self.max_value = ENDOWMENT
        self.n_steps = ENDOWMENT
        self.endowment = ENDOWMENT
        self.accumulated_score_me = int(accumulated_score_me)
        self.accumulated_score_partner = int(accumulated_score_partner)
        self.proposal = proposal
        self.round_payoff = int(round_payoff or 0)
        self.feedback = feedback
        self.round_failed = bool(round_failed)
        self.show_next = False

    def get_bot_response(self, experiment, bot, page, prompt):
        if self.phase == 'proposal':
            return _timeout_answer('proposal', str(int(RNG.integers(self.min_value, self.max_value + 1))))
        if self.phase == 'acceptance':
            if self.proposal in (None, 'No answer'):
                return None
            return _timeout_answer('acceptance', 'Accept' if RNG.random() < 0.5 else 'Reject')
        if self.phase == 'score':
            return str(self.round_payoff)
        return None
