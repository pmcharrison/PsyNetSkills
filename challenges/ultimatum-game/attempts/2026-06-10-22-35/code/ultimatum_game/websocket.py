import json

from psynet.timeline import NullElt, WebSocketElt
from psynet.utils import get_logger

from .game_parameters import ULTIMATUM_CHANNEL

logger = get_logger()


class EnableUltimatumWebSocket(NullElt, WebSocketElt):
    channel = ULTIMATUM_CHANNEL

    def handle_message(self, message, channel_name, participant, node, receive_time, experiment):
        # Waiting pages use this channel as a live wake-up signal; correctness is
        # still enforced by PsyNet GroupBarriers and page submissions.
        try:
            data = json.loads(message)
        except (TypeError, json.JSONDecodeError):
            return
        if data.get('type') == 'request_state' and participant is not None:
            publish_sync_event(
                {
                    'type': 'sync_event',
                    'event': 'state_ack',
                    'participant_id': participant.id,
                    'group_id': _group_id(participant),
                },
                experiment=experiment,
            )


def _group_id(participant):
    group = participant.active_sync_groups.get('chain') if participant is not None else None
    return group.id if group is not None else None


def publish_sync_event(payload, experiment=None):
    if experiment is None:
        from psynet.experiment import get_experiment
        experiment = get_experiment()
    payload.setdefault('type', 'sync_event')
    try:
        experiment.publish_to_subscribers(json.dumps(payload), channel_name=ULTIMATUM_CHANNEL)
    except Exception as exc:  # pragma: no cover - websocket backend may be absent in pure unit contexts
        logger.info('Could not publish ultimatum sync event: %s', exc)
