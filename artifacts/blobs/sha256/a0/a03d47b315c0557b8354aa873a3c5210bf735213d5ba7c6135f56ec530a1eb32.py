from psynet.trial.chain import ChainNode
from psynet.utils import get_logger

from .game_parameters import COIN_VALUE_DOLLARS, ENDOWMENT, MAX_TIMEOUT_ROUNDS, NUMBER_OF_ROUNDS
from .variable_handler import VariableHandler

logger = get_logger()


def initial_summary(participants=None):
    participant_ids = [str(p.id) for p in participants] if participants else []
    return {
        'counted_rounds': 0,
        'timeout_count': 0,
        'accumulated_rewards': {pid: 0 for pid in participant_ids},
        'history': [],
        'complete': False,
        'failed': False,
        'completion_reason': None,
    }


class GameNode(ChainNode):
    def create_initial_seed(self, experiment, participant):
        return self.seed

    def create_definition_from_seed(self, seed, experiment, participant):
        return seed

    def summarize_trials(self, trials, experiment, participant):
        valid_trials = [trial for trial in trials if not trial.failed]
        assert len(valid_trials) == 2, [trial.failed_reason for trial in trials]
        previous = self.definition.get('summary') or initial_summary([trial.participant for trial in valid_trials])
        rewards = {str(trial.participant_id): int(previous.get('accumulated_rewards', {}).get(str(trial.participant_id), 0)) for trial in valid_trials}
        history = list(previous.get('history', []))
        counted_rounds = int(previous.get('counted_rounds', 0))
        timeout_count = int(previous.get('timeout_count', 0))

        roles = {str(trial.participant_id): VariableHandler.get_value(trial.participant, 'round_role') for trial in valid_trials}
        proposer_trial = next((trial for trial in valid_trials if roles[str(trial.participant_id)] == 'proposer'), None)
        responder_trial = next((trial for trial in valid_trials if roles[str(trial.participant_id)] == 'responder'), None)
        proposal = self._first_answer(valid_trials, 'proposal')
        acceptance = self._first_answer(valid_trials, 'accept_answer')
        round_failed = any(self._trial_has_timeout(trial) for trial in valid_trials)
        timeout_role = self._timeout_role(valid_trials)
        payoffs = {str(trial.participant_id): 0 for trial in valid_trials}

        if round_failed:
            timeout_count += 1
            skipped = True
            decision = 'timeout'
        else:
            skipped = False
            decision = acceptance
            if acceptance == 'Accept':
                offer = int(proposal)
                payoffs[str(proposer_trial.participant_id)] = ENDOWMENT - offer
                payoffs[str(responder_trial.participant_id)] = offer
            for pid, payoff in payoffs.items():
                rewards[pid] = rewards.get(pid, 0) + payoff
            counted_rounds += 1

        last_round = {
            'attempt_index': len(history) + 1,
            'counted_rounds_after': counted_rounds,
            'skipped': skipped,
            'timeout_role': timeout_role if skipped else None,
            'roles': roles,
            'proposal': None if proposal == 'No answer' else proposal,
            'decision': decision,
            'payoffs': payoffs,
            'totals': dict(rewards),
        }
        history.append(last_round)

        complete = counted_rounds >= NUMBER_OF_ROUNDS
        failed = timeout_count > MAX_TIMEOUT_ROUNDS
        if failed:
            completion_reason = f'The pair exceeded {MAX_TIMEOUT_ROUNDS} decision timeouts.'
        elif complete:
            completion_reason = f'Completed {NUMBER_OF_ROUNDS} counted rounds.'
        else:
            completion_reason = None

        summary = {
            'counted_rounds': counted_rounds,
            'timeout_count': timeout_count,
            'accumulated_rewards': rewards,
            'history': history,
            'last_round': last_round,
            'complete': complete,
            'failed': failed,
            'completion_reason': completion_reason,
        }
        self.definition['summary'] = summary

        for trial in valid_trials:
            pid = str(trial.participant_id)
            trial.participant.var.ultimatum_score = rewards.get(pid, 0)
            trial.participant.var.ultimatum_history = history
            trial.participant.var.ultimatum_counted_rounds = counted_rounds
            trial.participant.var.ultimatum_timeout_count = timeout_count
            trial.participant.var.ultimatum_complete = complete or failed
            trial.participant.var.ultimatum_failed = failed
            trial.participant.var.ultimatum_completion_reason = completion_reason

        logger.info('Ultimatum node summary: %s', summary)
        return self.definition

    @staticmethod
    def _first_answer(trials, variable):
        for trial in trials:
            value = VariableHandler.get_from_answer(trial.answer, variable)
            if value is not None:
                return value
        return None

    @staticmethod
    def _trial_has_timeout(trial):
        if trial.answer and any(value == 'No answer' for value in trial.answer.values()):
            return True
        return bool(VariableHandler.get_value(trial.participant, 'round_failed'))

    @staticmethod
    def _timeout_role(trials):
        for trial in trials:
            role = VariableHandler.get_value(trial.participant, 'timeout_role')
            if role:
                return role
        return 'proposer'
