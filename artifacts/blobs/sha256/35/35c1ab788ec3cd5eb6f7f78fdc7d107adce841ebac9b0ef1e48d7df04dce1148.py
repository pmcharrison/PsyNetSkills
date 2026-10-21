import json
import random
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from dallinger import db
from psynet.data import SQLBase, SQLMixin, register_table
from psynet.participant import Participant

from .game_parameters import (
    COIN_VALUE_DOLLARS,
    ENDOWMENT,
    FEEDBACK_SECONDS,
    GLOBAL_CHANNEL,
    MAX_TIMEOUTS,
    PROPOSER_SECONDS,
    RESPONDER_SECONDS,
    ROUNDS_REQUIRED,
)


@register_table
class UltimatumSession(SQLBase, SQLMixin):
    __tablename__ = 'ultimatum_session'

    from sqlalchemy import Column, Integer, Text

    group_id = Column(Integer, unique=True, index=True)
    state_json = Column(Text)

    def __init__(self, group_id: int, state: Dict):
        self.group_id = group_id
        self.state = state

    @property
    def state(self) -> Dict:
        return json.loads(self.state_json)

    @state.setter
    def state(self, value: Dict):
        self.state_json = json.dumps(value)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


def participant_key(participant_or_id) -> str:
    return str(participant_or_id.id if hasattr(participant_or_id, 'id') else participant_or_id)


def make_deadline(seconds: int) -> str:
    return iso(utcnow() + timedelta(seconds=seconds))


def ordered_participant_ids(participants: List[Participant]) -> List[int]:
    return [participant.id for participant in sorted(participants, key=lambda p: p.id)]


def get_session(group_id: int) -> Optional[UltimatumSession]:
    return UltimatumSession.query.filter_by(failed=False, group_id=group_id).first()


def current_role_id(state: Dict, role: str) -> Optional[int]:
    for pid, assigned_role in state.get('roles', {}).items():
        if assigned_role == role:
            return int(pid)
    return None


def choose_roles(participant_ids: List[int]) -> Dict[str, str]:
    ids = list(participant_ids)
    random.shuffle(ids)
    return {str(ids[0]): 'proposer', str(ids[1]): 'responder'}


def public_state_for(state: Dict, participant_id: int) -> Dict:
    pid = participant_key(participant_id)
    return {
        'type': 'state_update',
        'target_participant_id': int(pid),
        'group_id': state['group_id'],
        'participant_id': int(pid),
        'round_index': state['round_index'],
        'counted_rounds': state['counted_rounds'],
        'rounds_required': state['rounds_required'],
        'status': state['status'],
        'role': state.get('roles', {}).get(pid),
        'roles': state.get('roles', {}),
        'offer': state.get('offer'),
        'decision': state.get('decision'),
        'deadline': state.get('deadline'),
        'feedback_until': state.get('feedback_until'),
        'last_round': state.get('last_round'),
        'total_score': state.get('totals', {}).get(pid, 0),
        'totals': state.get('totals', {}),
        'timeout_count': state.get('timeout_count', 0),
        'max_timeouts': state.get('max_timeouts', MAX_TIMEOUTS),
        'completion_reason': state.get('completion_reason'),
        'coin_value_dollars': COIN_VALUE_DOLLARS,
    }


def broadcast_state(experiment, state: Dict):
    for pid in state['participants']:
        experiment.publish_to_subscribers(
            json.dumps(public_state_for(state, pid)),
            channel_name=GLOBAL_CHANNEL,
        )


def start_decision_round(state: Dict):
    state['round_index'] += 1
    state['roles'] = choose_roles(state['participants'])
    state['status'] = 'proposal'
    state['offer'] = None
    state['decision'] = None
    state['feedback_acks'] = []
    state['last_round'] = None
    state['deadline'] = make_deadline(PROPOSER_SECONDS)
    state['events'].append(
        {
            'type': 'round_started',
            'round_index': state['round_index'],
            'roles': state['roles'],
            'deadline': state['deadline'],
        }
    )


def initialize_pair(group, participants: List[Participant]):
    participant_ids = ordered_participant_ids(participants)
    session = get_session(group.id)
    if session is None:
        state = {
            'group_id': group.id,
            'participants': participant_ids,
            'round_index': 0,
            'counted_rounds': 0,
            'rounds_required': ROUNDS_REQUIRED,
            'timeout_count': 0,
            'max_timeouts': MAX_TIMEOUTS,
            'totals': {str(pid): 0 for pid in participant_ids},
            'history': [],
            'events': [],
        }
        start_decision_round(state)
        db.session.add(UltimatumSession(group.id, state))
    for participant in participants:
        participant.var.ultimatum_score = 0
        participant.var.ultimatum_history = []
        participant.var.ultimatum_counted_rounds = 0
        participant.var.ultimatum_timeout_count = 0
        participant.var.ultimatum_complete = False
        participant.var.ultimatum_failed = False
        participant.var.ultimatum_bonus_applied = False
    db.session.commit()


def finish_round(state: Dict, accepted: bool):
    proposer_id = current_role_id(state, 'proposer')
    responder_id = current_role_id(state, 'responder')
    offer = int(state['offer'])
    if accepted:
        proposer_payoff = ENDOWMENT - offer
        responder_payoff = offer
    else:
        proposer_payoff = 0
        responder_payoff = 0
    payoffs = {str(proposer_id): proposer_payoff, str(responder_id): responder_payoff}
    for pid, payoff in payoffs.items():
        state['totals'][pid] = state['totals'].get(pid, 0) + payoff
    state['counted_rounds'] += 1
    state['decision'] = 'accept' if accepted else 'reject'
    state['last_round'] = {
        'round_index': state['round_index'],
        'skipped': False,
        'roles': dict(state['roles']),
        'offer': offer,
        'decision': state['decision'],
        'payoffs': payoffs,
        'totals': dict(state['totals']),
    }
    state['history'].append(state['last_round'])
    state['status'] = 'feedback'
    state['feedback_acks'] = []
    state['feedback_until'] = make_deadline(FEEDBACK_SECONDS)
    state['deadline'] = None


def skip_round_for_timeout(state: Dict, timed_out_role: str):
    state['timeout_count'] += 1
    state['last_round'] = {
        'round_index': state['round_index'],
        'skipped': True,
        'timeout_role': timed_out_role,
        'roles': dict(state['roles']),
        'offer': state.get('offer'),
        'decision': 'timeout',
        'payoffs': {str(pid): 0 for pid in state['participants']},
        'totals': dict(state['totals']),
    }
    state['history'].append(state['last_round'])
    state['deadline'] = None
    if state['timeout_count'] > state['max_timeouts']:
        state['status'] = 'failed'
        state['completion_reason'] = f'The pair exceeded the maximum of {MAX_TIMEOUTS} decision timeouts.'
    else:
        state['status'] = 'feedback'
        state['feedback_acks'] = []
        state['feedback_until'] = make_deadline(FEEDBACK_SECONDS)


def maybe_advance_after_feedback(state: Dict):
    both_acknowledged = set(state.get('feedback_acks', [])) == {str(pid) for pid in state['participants']}
    feedback_expired = state.get('feedback_until') and utcnow() >= parse_iso(state['feedback_until'])
    if not (both_acknowledged or feedback_expired):
        return
    if state['counted_rounds'] >= state['rounds_required']:
        state['status'] = 'complete'
        state['completion_reason'] = 'Completed all counted rounds.'
        state['deadline'] = None
        state['feedback_until'] = None
    else:
        start_decision_round(state)


def sync_participant_vars(state: Dict):
    participants = Participant.query.filter(Participant.id.in_(state['participants'])).all()
    for participant in participants:
        pid = str(participant.id)
        participant.var.ultimatum_score = state['totals'].get(pid, 0)
        participant.var.ultimatum_history = state['history']
        participant.var.ultimatum_counted_rounds = state['counted_rounds']
        participant.var.ultimatum_timeout_count = state['timeout_count']
        participant.var.ultimatum_complete = state['status'] in {'complete', 'failed'}
        participant.var.ultimatum_failed = state['status'] == 'failed'
        participant.var.ultimatum_completion_reason = state.get('completion_reason')


def process_action(experiment, participant: Participant, message: Dict):
    try:
        group_id = int(message.get('group_id'))
    except (TypeError, ValueError):
        return
    session = get_session(group_id)
    if session is None:
        return
    state = session.state
    pid = participant_key(participant)
    action = message.get('type')

    if pid not in {str(x) for x in state['participants']}:
        return

    if action in {'join', 'request_state'}:
        broadcast_state(experiment, state)
        return

    if state['status'] in {'complete', 'failed'}:
        broadcast_state(experiment, state)
        return

    if state.get('deadline') and utcnow() > parse_iso(state['deadline']):
        timeout_role = 'proposer' if state['status'] == 'proposal' else 'responder'
        skip_round_for_timeout(state, timeout_role)
        sync_participant_vars(state)
        session.state = state
        db.session.commit()
        broadcast_state(experiment, state)
        return

    if action == 'offer' and state['status'] == 'proposal':
        if state['roles'].get(pid) != 'proposer':
            return
        offer = int(message.get('offer'))
        if offer < 0 or offer > ENDOWMENT:
            return
        state['offer'] = offer
        state['status'] = 'response'
        state['deadline'] = make_deadline(RESPONDER_SECONDS)
        state['events'].append({'type': 'offer_submitted', 'round_index': state['round_index'], 'participant_id': int(pid), 'offer': offer})
    elif action == 'decision' and state['status'] == 'response':
        if state['roles'].get(pid) != 'responder':
            return
        decision = message.get('decision')
        if decision not in {'accept', 'reject'}:
            return
        finish_round(state, accepted=decision == 'accept')
        state['events'].append({'type': 'decision_submitted', 'round_index': state['round_index'], 'participant_id': int(pid), 'decision': decision})
    elif action == 'timeout':
        if state['status'] not in {'proposal', 'response'}:
            return
        if not state.get('deadline') or utcnow() < parse_iso(state['deadline']):
            return
        skip_round_for_timeout(state, 'proposer' if state['status'] == 'proposal' else 'responder')
    elif action == 'feedback_ack' and state['status'] == 'feedback':
        if pid not in state.get('feedback_acks', []):
            state.setdefault('feedback_acks', []).append(pid)
        maybe_advance_after_feedback(state)
    else:
        return

    sync_participant_vars(state)
    session.state = state
    db.session.commit()
    broadcast_state(experiment, state)


def apply_final_score(participant: Participant, answer: Dict):
    if participant.var.get('ultimatum_bonus_applied', False):
        return
    total_score = int(answer.get('total_score', participant.var.get('ultimatum_score', 0)))
    participant.var.ultimatum_score = total_score
    participant.var.ultimatum_bonus_applied = True
    participant.inc_performance_reward(total_score * COIN_VALUE_DOLLARS)


def simulate_complete_game(group_id: int) -> Dict:
    session = get_session(group_id)
    state = session.state
    if state['status'] == 'complete':
        return state
    scripted_offers = [2, 5, 1, 7, 4, 8, 3, 6, 0, 10, 5, 4]
    while state['counted_rounds'] < state['rounds_required']:
        if state['status'] != 'proposal':
            start_decision_round(state)
        state['offer'] = scripted_offers[(state['round_index'] - 1) % len(scripted_offers)]
        finish_round(state, accepted=state['offer'] >= 3)
        state['feedback_acks'] = [str(pid) for pid in state['participants']]
        maybe_advance_after_feedback(state)
    state['status'] = 'complete'
    state['completion_reason'] = 'Completed all counted rounds.'
    sync_participant_vars(state)
    session.state = state
    db.session.commit()
    return state


def simulate_timeout_failure(group_id: int) -> Dict:
    session = get_session(group_id)
    state = session.state
    while state['timeout_count'] <= state['max_timeouts']:
        skip_round_for_timeout(state, 'proposer' if state['status'] == 'proposal' else 'responder')
        if state['status'] == 'failed':
            break
        state['feedback_acks'] = [str(pid) for pid in state['participants']]
        maybe_advance_after_feedback(state)
    session.state = state
    db.session.commit()
    return state
