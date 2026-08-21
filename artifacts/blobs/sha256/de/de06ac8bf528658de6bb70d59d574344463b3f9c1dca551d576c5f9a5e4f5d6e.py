from markupsafe import Markup
from psynet.timeline import Page

from .custom_front_end import TimedModularPage, TimeoutPrompt, UltimatumControl
from .game_parameters import (
    ENDOWMENT,
    FEEDBACK_TIMEOUT,
    NUMBER_OF_ROUNDS,
    PROPOSER_TIMEOUT,
    RESPONDER_TIMEOUT,
    TIME_ESTIMATE_PER_ROUND,
    ULTIMATUM_CHANNEL,
    WAIT_PAGE_TIME,
)


class UltimatumWaitPage(Page):
    def __init__(self, *, content, round_, accumulated_score_me=0, accumulated_score_partner=0, phase='outer_waiting', proposal=None, wake_event='state_ack'):
        self.wait_time = WAIT_PAGE_TIME
        self.content = content
        self.round = round_
        self.accumulated_score_me = accumulated_score_me
        self.accumulated_score_partner = accumulated_score_partner
        self.phase = phase
        self.proposal = proposal
        self.wake_event = wake_event
        super().__init__(
            label='ultimatum_wait',
            time_estimate=WAIT_PAGE_TIME,
            template_path='templates/ultimatum-wait.html',
            template_arg=self._template_arg(None),
        )

    def _template_arg(self, group_id):
        return {
            'content': self.content,
            'round': self.round,
            'num_rounds': NUMBER_OF_ROUNDS,
            'accumulated_score_me': int(self.accumulated_score_me),
            'accumulated_score_partner': int(self.accumulated_score_partner),
            'phase': self.phase,
            'proposal': self.proposal,
            'endowment': ENDOWMENT,
            'wait_time': self.wait_time,
            'channel': ULTIMATUM_CHANNEL,
            'group_id': group_id,
            'wake_event': self.wake_event,
        }

    def render(self, experiment, participant):
        group = participant.active_sync_groups.get('chain')
        self.template_arg = self._template_arg(group.id if group else None)
        return super().render(experiment, participant)

    def get_bot_response(self, experiment, bot):
        return None

    def on_complete(self, experiment, participant):
        participant.total_wait_page_time += self.wait_time
        super().on_complete(experiment, participant)


class ProposalPage(TimedModularPage):
    def __init__(self, round_, accumulated_score_me=0, accumulated_score_partner=0):
        super().__init__(
            label='proposal',
            prompt=TimeoutPrompt(round_=round_, timeout=PROPOSER_TIMEOUT, text=Markup('<p>You are the proposer.</p>'), num_rounds=NUMBER_OF_ROUNDS),
            control=UltimatumControl('proposal', accumulated_score_me, accumulated_score_partner),
            time_estimate=TIME_ESTIMATE_PER_ROUND,
            save_answer='proposal',
            show_next_button=False,
        )

    def format_answer(self, raw_answer, **kwargs):
        participant = kwargs.get('participant')
        if raw_answer == 'No answer':
            if participant is not None:
                participant.var.round_failed = True
                participant.var.timeout_role = 'proposer'
            return 'No answer'
        return int(raw_answer)


class AcceptancePage(TimedModularPage):
    def __init__(self, proposal, round_, accumulated_score_me=0, accumulated_score_partner=0):
        super().__init__(
            label='accept_answer',
            prompt=TimeoutPrompt(round_=round_, timeout=RESPONDER_TIMEOUT, text=Markup('<p>You are the responder.</p>'), num_rounds=NUMBER_OF_ROUNDS),
            control=UltimatumControl('acceptance', accumulated_score_me, accumulated_score_partner, proposal=proposal),
            time_estimate=TIME_ESTIMATE_PER_ROUND,
            save_answer='accept_answer',
            show_next_button=False,
        )

    def format_answer(self, raw_answer, **kwargs):
        participant = kwargs.get('participant')
        if raw_answer == 'No answer':
            if participant is not None:
                participant.var.round_failed = True
                participant.var.timeout_role = 'responder'
            return 'No answer'
        if raw_answer not in {'Accept', 'Reject'}:
            return None
        return raw_answer


class ScorePage(TimedModularPage):
    def __init__(self, *, proposer, proposal, accepted, round_payoff, round_, accumulated_score_me, accumulated_score_partner, round_failed=False, timeout_role=None):
        if round_failed:
            feedback = f'Round skipped because the {timeout_role or "decision maker"} timed out. No coins were awarded and this round does not count.'
        elif accepted:
            if proposer:
                feedback = f'You offered {proposal} coins. The responder accepted, so you earned {round_payoff} coins.'
            else:
                feedback = f'You accepted an offer of {proposal} coins, so you earned {round_payoff} coins.'
        else:
            feedback = f'The responder rejected the offer of {proposal} coins. Both players earned 0 coins.'
        super().__init__(
            label='reward',
            prompt=TimeoutPrompt(round_=round_, timeout=FEEDBACK_TIMEOUT, text='', timeout_answer=str(round_payoff), num_rounds=NUMBER_OF_ROUNDS),
            control=UltimatumControl('score', accumulated_score_me, accumulated_score_partner, proposal=proposal, round_payoff=round_payoff, feedback=feedback, round_failed=round_failed),
            time_estimate=FEEDBACK_TIMEOUT,
            save_answer='reward',
            show_next_button=False,
        )
        self.round_payoff = int(round_payoff)

    def format_answer(self, raw_answer, **kwargs):
        return self.round_payoff
