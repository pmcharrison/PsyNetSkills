from psynet.trial.chain import ChainNode
from psynet.utils import get_logger

logger = get_logger()


class GameNode(ChainNode):
    def create_initial_seed(self, experiment, participant):
        return self.seed

    def create_definition_from_seed(self, seed, experiment, participant):
        return seed

    def summarize_trials(self, trials, experiment, participant):
        completed = [trial for trial in trials if not trial.failed]
        assert len(completed) == 2, [trial.failed_reason for trial in trials]
        answers = [trial.answer for trial in completed if trial.answer]
        summary = max(answers, key=lambda answer: answer.get('counted_rounds', 0))
        self.definition['summary'] = {
            'counted_rounds': summary.get('counted_rounds', 0),
            'timeout_count': summary.get('timeout_count', 0),
            'totals': summary.get('totals', {}),
            'last_round': summary.get('last_round'),
            'completion_reason': summary.get('completion_reason'),
        }
        logger.info('Ultimatum live-game node summary: %s', self.definition['summary'])
        return self.definition
