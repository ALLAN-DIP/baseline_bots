import random
from typing import List

from DAIDE import FCT
from diplomacy import Game, Message

from baseline_bots.bots.baseline_bot import BaselineMsgRoundBot
from baseline_bots.utils import MessagesAndOrders, MessagesData, OrdersData


class RandomHonestBot(BaselineMsgRoundBot):
    """
    This bot always acts randomly and truthfully communicates
    its intended moves in messages to all of its opponents
    """

    decided_this_round: bool

    def __init__(self, power_name: str, game: Game) -> None:
        super().__init__(power_name, game)
        self.decided_this_round = False

    def gen_messages(self, rcvd_messages: List[Message]) -> MessagesData:
        ret_obj = MessagesData()
        # orders will only change at next message round
        # for all other powers
        for other_power in [
            name for name in self.game.get_map_power_names() if name != self.power_name
        ]:
            # send the other power a message containing the orders
            ret_obj.add_message(other_power, str(FCT(self.orders)))

        return ret_obj

    def gen_orders(self) -> OrdersData:
        orders_ret_obj = OrdersData()
        possible_orders = self.game.get_all_possible_orders()
        random_orders = [
            random.choice(possible_orders[loc])
            for loc in self.game.get_orderable_locations(self.power_name)
            if possible_orders[loc]
        ]
        orders_ret_obj.add_orders(random_orders)
        return orders_ret_obj

    def phase_init(self) -> None:
        super().phase_init()
        self.decided_this_round = False

    def __call__(self, rcvd_messages: List[Message]) -> MessagesAndOrders:
        if not self.decided_this_round:
            self.orders = self.gen_orders()
            self.decided_this_round = True

        return {"orders": self.orders, "messages": self.gen_messages(rcvd_messages)}
