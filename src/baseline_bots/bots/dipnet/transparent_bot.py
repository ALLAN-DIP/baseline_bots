__author__ = "Kartik Shenoy"
__email__ = "kartik.shenoyy@gmail.com"

import random
from collections import defaultdict
from typing import List

from DAIDE import FCT, ORR, XDO
from diplomacy import Game, Message
from tornado import gen

from baseline_bots.bots.dipnet.dipnet_bot import DipnetBot
from baseline_bots.parsing_utils import daide_to_dipnet_parsing, dipnet_to_daide_parsing
from baseline_bots.utils import (
    MessagesData,
    get_other_powers,
    parse_arrangement,
    parse_FCT,
)


class TransparentBot(DipnetBot):
    """
    Execute orders computed by dipnet
    Send out some of them randomly
    """

    def __init__(self, power_name, game, total_msg_rounds=3):
        super().__init__(power_name, game, total_msg_rounds)
        self.orders_gossiped = set()
        self.my_orders_informed = False

    def phase_init(self) -> None:
        super().phase_init()
        self.orders_gossiped = set()
        self.my_orders_informed = False

    def parse_messages(self, rcvd_messages):
        press_msgs = [msg[1] for msg in rcvd_messages if "FCT" in msg[1].message]
        parsed_orders = []
        for msg in press_msgs:
            parsed_orders += parse_arrangement(parse_FCT(msg.message))
        return parsed_orders

    @gen.coroutine
    def gen_messages(self, rcvd_messages):
        # Fetch list of orders from DipNet
        orders = yield from self.brain.get_orders(self.game, self.power_name)
        self.orders.add_orders(orders, overwrite=True)
        self.my_orders_informed = False
        comms_obj = MessagesData()
        if self.game.get_current_phase()[-1] != "M":
            return comms_obj
        parsed_orders = self.parse_messages(rcvd_messages)
        parsed_orders = [
            list(daide_to_dipnet_parsing(order))[0]
            for order in parsed_orders
            if daide_to_dipnet_parsing(order)
        ]

        # My orders' messages if not already sent
        if not self.my_orders_informed:
            parsed_orders += self.orders.get_list_of_orders()
            self.my_orders_informed = True

        final_orders = []
        for order in parsed_orders:
            if order not in self.orders_gossiped:
                final_orders.append(order)
                self.orders_gossiped.add(order)

        for other_power in get_other_powers([self.power_name], self.game):
            if final_orders:
                msg = FCT(
                    ORR(
                        [
                            XDO(order)
                            for order in dipnet_to_daide_parsing(
                                final_orders, self.game
                            )
                        ]
                    )
                )
                comms_obj.add_message(other_power, str(msg))

        return comms_obj

    @gen.coroutine
    def gen_orders(self):
        """query dipnet for orders"""
        if self.game.get_current_phase()[-1] != "M":
            # Fetch list of orders from DipNet
            orders = yield from self.brain.get_orders(self.game, self.power_name)
            self.orders.add_orders(orders, overwrite=True)

        return self.orders.get_list_of_orders()

    @gen.coroutine
    def __call__(self, rcvd_messages: List[Message]):
        messages = yield from self.gen_messages(rcvd_messages)
        orders = yield from self.gen_orders()
        return {"messages": messages, "orders": orders}
