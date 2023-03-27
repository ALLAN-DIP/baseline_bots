import random

from tornado import gen

from baseline_bots.bots.baseline_bot import BaselineBot
from baseline_bots.utils import OrdersData


class RandomNoPressBot(BaselineBot):
    """
    Just execute random orders.
    """

    def __init__(self, power_name, game) -> None:
        super().__init__(power_name, game)
        self.orders = OrdersData()

    def gen_messages(self, rcvd_messages):
        return None

    def gen_orders(self):
        self.orders = OrdersData()
        possible_orders = self.game.get_all_possible_orders()

        orders = [
            random.choice([ord for ord in possible_orders[loc]])
            for loc in self.game.get_orderable_locations(self.power_name)
            if possible_orders[loc]
        ]

        self.orders.add_orders(orders)

        return self.orders.get_list_of_orders()


class RandomNoPress_AsyncBot(RandomNoPressBot):
    """Wrapper to RandomNoPressBot with tornado decorators for async calls"""

    @gen.coroutine
    def gen_messages(self, rcvd_messages):
        return super().gen_messages(rcvd_messages)

    @gen.coroutine
    def gen_orders(self):
        return super().gen_orders()
