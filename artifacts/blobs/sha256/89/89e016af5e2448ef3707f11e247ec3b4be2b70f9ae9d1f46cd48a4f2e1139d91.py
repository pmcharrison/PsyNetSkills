import json

from psynet.timeline import NullElt, WebSocketElt

from .game_parameters import GLOBAL_CHANNEL
from .game_state import process_action


class EnableUltimatumWebSocket(NullElt, WebSocketElt):
    channel = GLOBAL_CHANNEL

    def handle_message(self, message, channel_name, participant, node, receive_time, experiment):
        if participant is None:
            return
        try:
            payload = json.loads(message)
        except (TypeError, json.JSONDecodeError):
            return
        process_action(experiment, participant, payload)
