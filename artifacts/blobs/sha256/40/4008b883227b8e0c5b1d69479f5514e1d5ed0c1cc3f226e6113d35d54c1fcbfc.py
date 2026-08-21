from psynet.bot import BotResponse
from psynet.participant import Participant
from psynet.timeline import Page
from psynet.trial.chain import ChainTrial, ChainTrialMaker

from .game_parameters import COIN_VALUE_DOLLARS, GROUP_TYPE, ROUNDS_REQUIRED
from .game_state import apply_final_score, get_session, public_state_for, simulate_complete_game


class UltimatumGamePage(Page):
    def __init__(self, participant: Participant):
        group = participant.active_sync_groups[GROUP_TYPE]
        session = get_session(group.id)
        if session is None:
            raise RuntimeError('Ultimatum session was not initialized.')
        state = session.state
        super().__init__(
            label='ultimatum_game',
            template_path='templates/ultimatum-game.html',
            time_estimate=max(60, ROUNDS_REQUIRED * 25),
            save_answer='ultimatum_final',
            js_vars={
                'ultimatum_group_id': group.id,
                'ultimatum_participant_id': participant.id,
                'ultimatum_initial_state': public_state_for(state, participant.id),
            },
        )

    def get_bot_response(self, experiment, bot):
        participant = Participant.query.get(bot.id)
        state = simulate_complete_game(participant.active_sync_groups[GROUP_TYPE].id)
        return BotResponse(raw_answer=public_state_for(state, bot.id))

    def format_answer(self, raw_answer, **kwargs):
        participant = kwargs['participant']
        answer = raw_answer or {}
        if isinstance(answer, dict):
            apply_final_score(participant, answer)
        return answer


class GameTrial(ChainTrial):
    time_estimate = max(60, ROUNDS_REQUIRED * 25)

    def show_trial(self, experiment, participant):
        return UltimatumGamePage(participant)

    def score_answer(self, answer, definition):
        return 0

    def compute_performance_reward(self, score):
        return 0


class GameTrialMaker(ChainTrialMaker):
    def on_complete(self, experiment, participant):
        if not participant.var.get('ultimatum_bonus_applied', False):
            score = int(participant.var.get('ultimatum_score', 0))
            participant.inc_performance_reward(score * COIN_VALUE_DOLLARS)
            participant.var.ultimatum_bonus_applied = True
