from typing import ClassVar, List

from diplomacy.utils import strings
from tornado import gen

from baseline_bots.bots.dipnet_bot import DipnetBot


class NoPressDipBot(DipnetBot):
    """just execute orders computed by dipnet"""

    player_type: ClassVar[str] = strings.NO_PRESS_BOT

    @gen.coroutine
    def __call__(self) -> List[str]:
        orders = yield self.gen_orders()
        return orders
