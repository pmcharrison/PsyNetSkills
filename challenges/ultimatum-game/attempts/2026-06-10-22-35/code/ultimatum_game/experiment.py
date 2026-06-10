from dominate import tags
from markupsafe import Markup

import psynet.experiment
from psynet.page import InfoPage, SuccessfulEndPage, UnsuccessfulEndPage
from psynet.timeline import PageMaker, Timeline

from .custom_barriers import CustomBarrier, CustomSimpleGrouper
from .custom_pages import UltimatumWaitPage
from .game_node import GameNode
from .game_parameters import (
    BASE_PAYMENT,
    COIN_VALUE_DOLLARS,
    CURRENCY,
    ENDOWMENT,
    ESTIMATED_DURATION,
    HOURLY_PAYMENT,
    MAX_ATTEMPTED_ROUNDS,
    MAX_TIMEOUT_ROUNDS,
    NUMBER_OF_ROUNDS,
    TARGET_PARTICIPANTS,
    TIMEOUT_WAITING_FOR_OTHER,
    TIME_ESTIMATE_PER_ROUND,
)
from .game_trial import GameTrial, GameTrialMaker
from .websocket import EnableUltimatumWebSocket


def assign_roles(group, participants):
    from .game_parameters import RNG
    roles = ['proposer', 'responder']
    RNG.shuffle(roles)
    for participant, role in zip(sorted(participants, key=lambda p: p.id), roles):
        participant.var.role = role
        participant.var.round_role = role
        participant.var.round_failed = False
        participant.var.timeout_role = None
        participant.var.ultimatum_score = 0
        participant.var.ultimatum_counted_rounds = 0
        participant.var.ultimatum_timeout_count = 0
        participant.var.ultimatum_complete = False
        participant.var.ultimatum_failed = False
        participant.var.ultimatum_bonus_applied = False


def get_start_nodes():
    return [
        GameNode(
            definition={'transition': 'random'},
            context={},
        )
    ]


def instructions_page():
    content = tags.div()
    with content:
        tags.h2('Repeated Ultimatum game')
        tags.p('You will be paired with one other participant and play repeated synchronous rounds.')
        tags.ul(
            tags.li(f'Each counted round has a {ENDOWMENT}-coin endowment.'),
            tags.li('Every round randomly assigns one proposer and one responder; roles can change from round to round.'),
            tags.li('The proposer uses a slider to offer 0 to 10 coins to the responder.'),
            tags.li('If the responder accepts, the responder gets the offered coins and the proposer keeps the rest.'),
            tags.li('If the responder rejects, both players earn 0 coins for that round.'),
        )
        tags.p(
            f'You must complete {NUMBER_OF_ROUNDS} counted rounds together. Decision timers do not reset if the browser refreshes. '
            'If either player times out during a proposal or response decision, that round is skipped, no coins are added, '
            f'and the skipped round does not count toward the {NUMBER_OF_ROUNDS} required counted rounds. The pair fails after more than {MAX_TIMEOUT_ROUNDS} decision timeouts.'
        )
        tags.p(f'Your performance bonus is ${COIN_VALUE_DOLLARS:.2f} per coin earned across counted rounds.')
    return InfoPage(content, time_estimate=45)


def partner_wait_page(participant):
    return UltimatumWaitPage(
        content=Markup('<h3>Waiting for a partner</h3><p>You will start as soon as another participant joins.</p>'),
        round_=1,
        phase='outer_waiting',
        wake_event='state_ack',
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
        'wage_per_hour': HOURLY_PAYMENT,
        'currency': CURRENCY,
        'show_reward': True,
        'show_progress_bar': False,
        'title': f'Ultimatum game ({NUMBER_OF_ROUNDS} counted rounds)',
        'description': 'A two-player repeated Ultimatum game with synchronized proposer and responder decisions.',
        'prolific_estimated_completion_minutes': ESTIMATED_DURATION,
    }

    timeline = Timeline(
        EnableUltimatumWebSocket(),
        PageMaker(instructions_page, time_estimate=45),
        CustomSimpleGrouper(
            group_type='chain',
            initial_group_size=2,
            max_group_size='initial_group_size',
            min_group_size=2,
            join_existing_groups=False,
            waiting_logic=PageMaker(partner_wait_page, time_estimate=5),
            max_wait_time=TIMEOUT_WAITING_FOR_OTHER,
        ),
        CustomBarrier(
            id_='assign_roles',
            content='Assigning roles...',
            on_release=assign_roles,
            max_wait_time=TIMEOUT_WAITING_FOR_OTHER,
        ),
        GameTrialMaker(
            id_='ultimatum_trial_maker',
            trial_class=GameTrial,
            node_class=GameNode,
            chain_type='within',
            start_nodes=get_start_nodes,
            expected_trials_per_participant=NUMBER_OF_ROUNDS,
            max_trials_per_participant=MAX_ATTEMPTED_ROUNDS,
            chains_per_participant=1,
            target_n_participants=TARGET_PARTICIPANTS,
            wait_for_networks=True,
            max_nodes_per_chain=MAX_ATTEMPTED_ROUNDS,
            trials_per_node=2,
            sync_group_type='chain',
            sync_group_max_wait_time=TIMEOUT_WAITING_FOR_OTHER,
        ),
        PageMaker(completion_page, time_estimate=10),
        SuccessfulEndPage(),
    )

    def test_serial_run_bots(self, bots):
        for bot in bots:
            assert 'Repeated Ultimatum game' in bot.current_page_text
            bot.take_page()
        for _ in range(400):
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
        from psynet.participant import Participant
        from .game_trial import GameTrial

        participants = Participant.query.filter(Participant.id.in_([bot.id for bot in bots])).all()
        assert len(participants) == 2
        for participant in participants:
            assert participant.var.ultimatum_counted_rounds == NUMBER_OF_ROUNDS
            assert participant.var.ultimatum_score >= 0
            assert participant.var.ultimatum_bonus_applied
            expected_reward = participant.var.ultimatum_score * COIN_VALUE_DOLLARS
            assert abs(participant.performance_reward - expected_reward) < 1e-9

        trials = GameTrial.query.filter_by(failed=False).all()
        assert len(trials) >= NUMBER_OF_ROUNDS * 2
        summaries = [trial.definition.get('summary') for trial in trials if trial.definition.get('summary')]
        assert summaries
        final = summaries[-1]
        assert final['counted_rounds'] == NUMBER_OF_ROUNDS
        assert len({tuple(round_['roles'].values()) for round_ in final['history']}) >= 1
        assert any(round_['decision'] in {'Accept', 'Reject'} for round_ in final['history'])
