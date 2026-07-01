from psynet.page import WaitPage
from psynet.sync import GroupBarrier, SimpleGrouper

from .game_parameters import TIMEOUT_WAITING_FOR_OTHER, WAIT_PAGE_TIME


class CustomBarrier(GroupBarrier):
    def __init__(self, id_, content=None, active_participant=None, wait_page=None, on_release=None, max_wait_time=TIMEOUT_WAITING_FOR_OTHER):
        if wait_page is None:
            wait_page = WaitPage(wait_time=WAIT_PAGE_TIME, content=content or 'Waiting for your partner...')
        if active_participant:
            wait_page = WaitPage(wait_time=0.2, content='Moving on...')
        super().__init__(
            id_=id_,
            group_type='chain',
            waiting_logic=wait_page,
            waiting_logic_expected_repetitions=1,
            max_wait_time=max_wait_time,
            on_release=on_release,
            fix_time_credit=True,
        )


class CustomSimpleGrouper(SimpleGrouper):
    pass
