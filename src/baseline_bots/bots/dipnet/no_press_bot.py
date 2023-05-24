from typing import List

from tornado import gen

from baseline_bots.bots.dipnet.dipnet_bot import DipnetBot


class NoPressDipBot(DipnetBot):
    """just execute orders computed by dipnet"""

    @gen.coroutine
    def __call__(self) -> List[str]:
        orders = yield self.gen_orders()
        return orders
