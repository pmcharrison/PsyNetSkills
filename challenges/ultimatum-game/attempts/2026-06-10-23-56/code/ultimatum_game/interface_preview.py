import psynet.experiment
from psynet.bot import BotResponse
from psynet.timeline import Page, Timeline


class UltimatumInterfacePreviewPage(Page):
    def __init__(self):
        super().__init__(
            label='ultimatum_interface_preview',
            template_path='templates/ultimatum-game.html',
            time_estimate=30,
            save_answer='ultimatum_interface_preview',
            js_vars={
                'ultimatum_group_id': 0,
                'ultimatum_participant_id': 1,
                'ultimatum_initial_state': {
                    'type': 'state_update',
                    'target_participant_id': 1,
                    'group_id': 0,
                    'participant_id': 1,
                    'round_index': 1,
                    'counted_rounds': 0,
                    'rounds_required': 10,
                    'status': 'proposal',
                    'role': 'proposer',
                    'roles': {'1': 'proposer', '2': 'responder'},
                    'offer': None,
                    'decision': None,
                    'deadline': None,
                    'feedback_until': None,
                    'last_round': None,
                    'total_score': 0,
                    'totals': {'1': 0, '2': 0},
                    'timeout_count': 0,
                    'max_timeouts': 5,
                    'coin_value_dollars': 0.01,
                },
            },
        )

    def get_bot_response(self, experiment, bot):
        return BotResponse(raw_answer={'status': 'previewed'})


preview_timeline = Timeline(UltimatumInterfacePreviewPage())


class InterfacePreviewExperiment(psynet.experiment.Experiment):
    label = 'Ultimatum interface preview'
    timeline = preview_timeline
