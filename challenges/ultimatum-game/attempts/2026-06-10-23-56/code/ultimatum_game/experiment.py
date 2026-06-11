from dominate import tags

import psynet.experiment
from dallinger import db
from dallinger.experiment import experiment_route
from dallinger.experiment_server.utils import success_response
from flask import request
from psynet.page import InfoPage, WaitPage
from psynet.participant import Participant
from psynet.sync import GroupBarrier, SimpleGrouper
from psynet.timeline import PageMaker, Timeline

from .game_node import GameNode
from .game_parameters import (
    BASE_PAYMENT,
    COIN_VALUE_DOLLARS,
    CURRENCY,
    ENDOWMENT,
    ESTIMATED_DURATION,
    GROUP_TYPE,
    MAX_TIMEOUTS,
    ROUNDS_REQUIRED,
    TARGET_PARTICIPANTS,
)
from .game_state import UltimatumSession, initialize_pair, make_deadline, process_action, simulate_timeout_failure
from .game_trial import GameTrial, GameTrialMaker
from .websocket import EnableUltimatumWebSocket


def get_start_nodes():
    return [GameNode(definition={'flow': 'live_websocket'}, context={})]


def instructions_page():
    content = tags.div()
    with content:
        tags.h2('Repeated Ultimatum game')
        tags.p(f'You will be paired with another participant and play until you complete {ROUNDS_REQUIRED} scored rounds together.')
        tags.ul(
            tags.li('Each round randomly assigns one proposer and one responder; roles can change from round to round.'),
            tags.li(f'The proposer divides a {ENDOWMENT}-coin endowment by offering 0 to 10 coins.'),
            tags.li('If the responder accepts, the responder earns the offer and the proposer keeps the rest.'),
            tags.li('If the responder rejects, both players earn 0 coins for that round.'),
            tags.li('If either player times out, the round is skipped and does not count.'),
        )
        tags.p(f'The pair fails after more than {MAX_TIMEOUTS} decision timeouts.')
        tags.p(f'Your performance bonus is ${COIN_VALUE_DOLLARS:.2f} per coin earned across counted rounds.')
    return InfoPage(content, time_estimate=45)


def waiting_page(participant):
    return WaitPage(
        content='Waiting for a partner. You will start as soon as another participant joins.',
        wait_time=1.0,
    )


def completion_page(participant):
    total = int(participant.var.get('ultimatum_score', 0))
    counted = int(participant.var.get('ultimatum_counted_rounds', 0))
    timeouts = int(participant.var.get('ultimatum_timeout_count', 0))
    failed = bool(participant.var.get('ultimatum_failed', False))
    reason = participant.var.get('ultimatum_completion_reason', None)
    content = tags.div()
    with content:
        tags.h2('Task complete' if not failed else 'Task ended')
        tags.p(f'Your total score is {total} coins from {counted} counted rounds.')
        tags.p(f'Your performance bonus is {total} x ${COIN_VALUE_DOLLARS:.2f} = ${total * COIN_VALUE_DOLLARS:.2f}.')
        tags.p(f'The pair recorded {timeouts} decision timeout(s). Skipped timeout rounds did not add coins or count toward the required rounds.')
        if reason:
            tags.p(reason)
    return InfoPage(content, time_estimate=10)


class Exp(psynet.experiment.Experiment):
    label = 'Repeated Ultimatum game'
    test_n_bots = 2
    test_mode = 'serial'

    config = {
        'recruiter': 'hotair',
        'initial_recruitment_size': 2,
        'base_payment': BASE_PAYMENT,
        'wage_per_hour': 12,
        'currency': CURRENCY,
        'show_reward': True,
        'show_progress_bar': False,
        'title': f'Ultimatum game ({ROUNDS_REQUIRED} counted rounds)',
        'description': 'A two-player repeated Ultimatum game with WebSocket synchronization inside PsyNet ChainTrialMaker/ChainNode constructs.',
        'prolific_estimated_completion_minutes': ESTIMATED_DURATION,
    }

    timeline = Timeline(
        EnableUltimatumWebSocket(),
        PageMaker(instructions_page, time_estimate=45),
        SimpleGrouper(
            group_type=GROUP_TYPE,
            initial_group_size=2,
            max_group_size='initial_group_size',
            min_group_size=2,
            join_existing_groups=False,
            waiting_logic=PageMaker(waiting_page, time_estimate=5),
            max_wait_time=120,
        ),
        GroupBarrier(
            id_='initialize_ultimatum_pair',
            group_type=GROUP_TYPE,
            waiting_logic=PageMaker(waiting_page, time_estimate=5),
            max_wait_time=60,
            on_release=initialize_pair,
        ),
        GameTrialMaker(
            id_='ultimatum_trial_maker',
            trial_class=GameTrial,
            node_class=GameNode,
            chain_type='within',
            start_nodes=get_start_nodes,
            expected_trials_per_participant=1,
            max_trials_per_participant=1,
            chains_per_participant=1,
            target_n_participants=TARGET_PARTICIPANTS,
            wait_for_networks=True,
            max_nodes_per_chain=1,
            trials_per_node=2,
            sync_group_type=GROUP_TYPE,
            sync_group_max_wait_time=60,
        ),
        PageMaker(completion_page, time_estimate=10),
    )

    @experiment_route('/ultimatum_action', methods=['POST'])
    @classmethod
    def ultimatum_action(cls):
        from psynet.experiment import get_experiment

        msg = request.get_json(silent=True) or {}
        participant = Participant.query.filter_by(id=msg.get('participant_id')).first()
        if participant is None or participant.unique_id != msg.get('unique_id'):
            return success_response(ok=False)
        process_action(get_experiment(), participant, msg)
        return success_response(ok=True)

    def test_serial_run_bots(self, bots):
        for bot in bots:
            assert 'Repeated Ultimatum game' in bot.current_page_text
            bot.take_page()
        for _ in range(100):
            if all(not bot.is_working for bot in bots):
                break
            for bot in bots:
                if bot.is_working:
                    bot.take_page()
        else:
            labels = [bot.current_page_label for bot in bots]
            raise AssertionError(f'Bots did not complete the synchronized ultimatum flow; labels={labels}.')
        assert all(not bot.is_working for bot in bots)

    def test_check_bots(self, bots):
        participants = Participant.query.filter(Participant.id.in_([bot.id for bot in bots])).all()
        assert len(participants) == 2
        for participant in participants:
            assert participant.var.ultimatum_counted_rounds == ROUNDS_REQUIRED
            assert participant.var.ultimatum_score >= 0
            assert participant.var.ultimatum_bonus_applied
            expected_reward = participant.var.ultimatum_score * COIN_VALUE_DOLLARS
            assert abs(participant.performance_reward - expected_reward) < 1e-9

        trials = GameTrial.query.filter_by(failed=False).all()
        assert len(trials) == 2
        assert all(trial.answer for trial in trials)
        node_summaries = [trial.definition.get('summary') for trial in trials if trial.definition.get('summary')]
        assert node_summaries
        assert max(summary['counted_rounds'] for summary in node_summaries) == ROUNDS_REQUIRED

        state = {
            'group_id': 999999,
            'participants': [991, 992],
            'round_index': 1,
            'counted_rounds': 0,
            'rounds_required': ROUNDS_REQUIRED,
            'timeout_count': 0,
            'max_timeouts': MAX_TIMEOUTS,
            'totals': {'991': 0, '992': 0},
            'history': [],
            'events': [],
            'roles': {'991': 'proposer', '992': 'responder'},
            'status': 'proposal',
            'offer': None,
            'decision': None,
            'deadline': make_deadline(-1),
        }
        db.session.add(UltimatumSession(999999, state))
        db.session.commit()
        failed_state = simulate_timeout_failure(999999)
        assert failed_state['status'] == 'failed'
        assert failed_state['timeout_count'] == MAX_TIMEOUTS + 1
        assert failed_state['counted_rounds'] == 0
