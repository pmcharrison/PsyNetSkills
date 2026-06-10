from markupsafe import Markup
from psynet.timeline import CodeBlock, conditional, join
from psynet.trial.chain import ChainTrial, ChainTrialMaker

from .custom_barriers import CustomBarrier
from .custom_pages import AcceptancePage, ProposalPage, ScorePage, UltimatumWaitPage
from .game_node import initial_summary
from .game_parameters import COIN_VALUE_DOLLARS, ENDOWMENT, MAX_ATTEMPTED_ROUNDS, MAX_TIMEOUT_ROUNDS, NUMBER_OF_ROUNDS, RNG, TIME_ESTIMATE_PER_ROUND
from .variable_handler import VariableHandler
from .websocket import publish_sync_event


class GameTrial(ChainTrial):
    time_estimate = TIME_ESTIMATE_PER_ROUND
    accumulate_answers = True

    def show_trial(self, experiment, participant):
        return join(
            CodeBlock(self.prepare_round),
            CustomBarrier(
                id_='start_round',
                active_participant=False,
                wait_page=self.outer_wait_page('Preparing the next round...', 'round_started'),
            ),
            self.ultimatum_game(),
            self.show_trial_feedback(),
            CustomBarrier(
                id_='show_score',
                active_participant=False,
                on_release=self.choose_new_role,
                wait_page=self.outer_wait_page('Waiting for both players to finish feedback...', 'score_seen'),
            ),
        )

    def prepare_round(self, participant):
        participant.var.round_failed = False
        participant.var.timeout_role = None
        participant.var.proposal = None
        participant.var.accept_answer = None
        participant.var.round_role = self.get_role(participant)

    def ultimatum_game(self):
        return join(
            self.proposal_stage(),
            conditional(
                label='round_not_failed_before_response',
                condition=lambda participant: not self.did_round_fail(),
                logic_if_true=self.acceptance_stage(),
                logic_if_false=None,
            ),
        )

    def proposal_stage(self):
        return join(
            conditional(
                label='proposer_action',
                condition=lambda participant: self.is_proposer(participant),
                logic_if_true=ProposalPage(
                    round_=self.visible_round_number(),
                    accumulated_score_me=self.get_my_score(),
                    accumulated_score_partner=self.get_partner_score(),
                ),
                logic_if_false=None,
            ),
            CustomBarrier(
                id_='proposal_stage',
                active_participant=False,
                on_release=self.assign_proposal,
                wait_page=self.outer_wait_page('Waiting for the proposer to submit an offer...', 'proposal_submitted'),
            ),
        )

    def acceptance_stage(self):
        return join(
            conditional(
                label='responder_action',
                condition=lambda participant: self.is_responder(participant),
                logic_if_true=AcceptancePage(
                    proposal=self.get_proposal(),
                    round_=self.visible_round_number(),
                    accumulated_score_me=self.get_my_score(),
                    accumulated_score_partner=self.get_partner_score(),
                ),
                logic_if_false=None,
            ),
            CustomBarrier(
                id_='acceptance_stage',
                active_participant=False,
                on_release=self.record_decision,
                wait_page=self.inner_wait_page('Waiting for the responder to accept or reject...', 'decision_submitted'),
            ),
        )

    def assign_proposal(self, group=None, participants=None):
        participants = list(participants or self.participant.sync_group.participants)
        proposal = None
        for participant in participants:
            if self.is_proposer(participant):
                proposal = VariableHandler.get_value_from_last_answer(participant, 'proposal')
                if proposal == 'No answer':
                    self.mark_round_failed(participants, 'proposer')
                break
        for participant in participants:
            participant.var.proposal = proposal
        publish_sync_event({'event': 'proposal_submitted', 'group_id': group.id if group else None, 'proposal': proposal})

    def record_decision(self, group=None, participants=None):
        participants = list(participants or self.participant.sync_group.participants)
        decision = None
        for participant in participants:
            if self.is_responder(participant):
                decision = VariableHandler.get_value_from_last_answer(participant, 'accept_answer')
                if decision == 'No answer':
                    self.mark_round_failed(participants, 'responder')
                break
        for participant in participants:
            participant.var.accept_answer = decision
        publish_sync_event({'event': 'decision_submitted', 'group_id': group.id if group else None, 'decision': decision})

    @staticmethod
    def mark_round_failed(participants, timeout_role):
        for participant in participants:
            participant.var.round_failed = True
            participant.var.timeout_role = timeout_role

    def show_trial_feedback(self):
        proposer = self.am_i_proposer()
        proposal = self.get_proposal()
        accepted = self.get_acceptance() == 'Accept'
        round_failed = self.did_round_fail()
        if round_failed or proposal in (None, 'No answer'):
            payoff = 0
            proposal_for_page = 0 if proposal in (None, 'No answer') else int(proposal)
        elif accepted:
            proposal_for_page = int(proposal)
            payoff = ENDOWMENT - proposal_for_page if proposer else proposal_for_page
        else:
            proposal_for_page = int(proposal)
            payoff = 0
        return ScorePage(
            proposer=proposer,
            proposal=proposal_for_page,
            accepted=accepted,
            round_payoff=payoff,
            round_=self.visible_round_number(),
            accumulated_score_me=self.get_my_score() + payoff,
            accumulated_score_partner=self.get_partner_score() + self.partner_payoff(proposal_for_page, accepted, round_failed),
            round_failed=round_failed,
            timeout_role=VariableHandler.get_value(self.participant, 'timeout_role'),
        )

    def choose_new_role(self, group=None, participants=None):
        participants = sorted(list(participants or self.participant.sync_group.participants), key=lambda p: p.id)
        roles = ['proposer', 'responder']
        RNG.shuffle(roles)
        for participant, role in zip(participants, roles):
            participant.var.role = role
        publish_sync_event({'event': 'roles_assigned', 'group_id': group.id if group else None})

    def outer_wait_page(self, content, wake_event):
        return UltimatumWaitPage(
            content=Markup(f'<h3>{content}</h3><p>Please keep this browser tab open.</p>'),
            round_=self.visible_round_number(),
            accumulated_score_me=self.get_my_score(),
            accumulated_score_partner=self.get_partner_score(),
            phase='outer_waiting',
            wake_event=wake_event,
        )

    def inner_wait_page(self, content, wake_event):
        return UltimatumWaitPage(
            content=Markup(f'<h3>{content}</h3><p>Your offer is visible while your partner decides.</p>'),
            round_=self.visible_round_number(),
            accumulated_score_me=self.get_my_score(),
            accumulated_score_partner=self.get_partner_score(),
            phase='inner_waiting',
            proposal=self.get_proposal(),
            wake_event=wake_event,
        )

    def previous_summary(self):
        return self.definition.get('summary') or initial_summary(self.participant.sync_group.participants)

    def visible_round_number(self):
        return min(NUMBER_OF_ROUNDS, int(self.previous_summary().get('counted_rounds', 0)) + 1)

    def get_role(self, participant):
        return VariableHandler.get_value(participant, 'role')

    def am_i_proposer(self):
        return self.is_proposer(self.participant)

    def is_proposer(self, participant):
        return self.get_role(participant) == 'proposer'

    def is_responder(self, participant):
        return self.get_role(participant) == 'responder'

    def get_proposal(self):
        proposal = VariableHandler.get_value(self.participant, 'proposal')
        if proposal is None:
            proposal = self._partner_var('proposal')
        return proposal

    def get_acceptance(self):
        answer = VariableHandler.get_value(self.participant, 'accept_answer')
        if answer is None:
            answer = self._partner_var('accept_answer')
        return answer

    def _partner_var(self, variable):
        for participant in self.participant.sync_group.participants:
            value = VariableHandler.get_value(participant, variable)
            if value is not None:
                return value
        return None

    def did_round_fail(self):
        return any(bool(VariableHandler.get_value(p, 'round_failed')) for p in self.participant.sync_group.participants)

    def get_my_score(self):
        summary = self.previous_summary()
        return int(summary.get('accumulated_rewards', {}).get(str(self.participant.id), 0))

    def get_partner_score(self):
        summary = self.previous_summary()
        scores = summary.get('accumulated_rewards', {})
        return sum(int(score) for pid, score in scores.items() if int(pid) != self.participant.id)

    def partner_payoff(self, proposal, accepted, round_failed):
        if round_failed or not accepted:
            return 0
        return proposal if self.am_i_proposer() else ENDOWMENT - proposal

    def score_answer(self, answer, definition):
        return 0

    def compute_performance_reward(self, score):
        return 0


class GameTrialMaker(ChainTrialMaker):
    def prepare_trial(self, experiment, participant):
        if participant.var.get('ultimatum_complete', False):
            return None, 'exit'
        if participant.var.get('ultimatum_timeout_count', 0) > MAX_TIMEOUT_ROUNDS:
            participant.var.ultimatum_complete = True
            participant.var.ultimatum_failed = True
            return None, 'exit'
        return super().prepare_trial(experiment, participant)

    def on_complete(self, experiment, participant):
        if not participant.var.get('ultimatum_bonus_applied', False):
            score = int(participant.var.get('ultimatum_score', 0))
            participant.inc_performance_reward(score * COIN_VALUE_DOLLARS)
            participant.var.ultimatum_bonus_applied = True
