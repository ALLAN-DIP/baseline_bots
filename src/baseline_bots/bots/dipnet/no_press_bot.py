from typing import List

from diplomacy import Message
from tornado import gen

from baseline_bots.bots.dipnet.dipnet_bot import DipnetBot
from baseline_bots.utils import OrdersData


class NoPressDipBot(DipnetBot):
    """just execute orders computed by dipnet"""

    @gen.coroutine
    def gen_messages(self, rcvd_messages: List[Message]) -> None:
        """query dipnet for orders"""
        return None

    @gen.coroutine
    def gen_orders(self) -> List[str]:
        self.orders = OrdersData()
        orders = yield self.brain.get_orders(self.game, self.power_name)
        self.orders.add_orders(orders, overwrite=True)
        return self.orders.get_list_of_orders()

    @gen.coroutine
    def __call__(self, rcvd_messages: List[Message]) -> dict:
        return {
            "messages": self.gen_messages(rcvd_messages),
            "orders": self.gen_orders(),
        }
