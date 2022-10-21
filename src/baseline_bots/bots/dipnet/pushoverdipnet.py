__authors__ = "Wichayaporn Wongkamjan"
__email__ = "w.wongkamjan@gmail.com"


import random
from typing import List

from DAIDE import FCT, ORR, XDO, ParseError
from diplomacy import Game, Message
from diplomacy_research.players.benchmark_player import DipNetRLPlayer
from tornado import gen

from baseline_bots.bots.dipnet.dipnet_bot import DipnetBot
from baseline_bots.utils import (
    REJ,
    YES,
    MessagesData,
    OrdersData,
    get_non_aggressive_orders,
    get_order_tokens,
    get_other_powers,
    parse_arrangement,
    parse_FCT,
    sort_messages_by_most_recent,
)


class PushoverDipnet(DipnetBot):
    """
    Moves by Dipnet's orders and replace its own orders by the last proposal (if exists)
    NOTE: only executes non-aggressive action
    """

    def __init__(self, power_name: str, game: Game, total_msg_rounds=3) -> None:
        super().__init__(power_name, game, total_msg_rounds)

    @gen.coroutine
    def gen_messages(self, rcvd_messages):
        self.orders = OrdersData()
        reply_obj = MessagesData()

        orders = yield self.brain.get_orders(self.game, self.power_name)
        self.orders.add_orders(orders, overwrite=True)

        if len(rcvd_messages) == 0:
            return reply_obj

        sorted_rcvd_messages = sort_messages_by_most_recent(rcvd_messages)
        last_message = sorted_rcvd_messages[0]
        while "FCT" in last_message.message:
            sorted_rcvd_messages.pop(0)
            if len(sorted_rcvd_messages) == 0:
                break
            last_message = sorted_rcvd_messages[0]

        if "FCT" in last_message.message or len(sorted_rcvd_messages) == 0:
            return reply_obj

        # parse may fail
        try:
            # print(last_message.message)
            # print(parse_arrangement(last_message.message))
            orders = get_non_aggressive_orders(
                parse_arrangement(last_message.message), self.power_name, self.game
            )
            # set the orders
            self.orders.add_orders(orders, overwrite=True)

            # set message to say YES
            msg = YES(last_message.message)
            reply_obj.add_message(last_message.sender, str(msg))

            for message in sorted_rcvd_messages[1:]:
                if "FCT" not in last_message.message:
                    msg = REJ(message)
                    reply_obj.add_message(message.sender, str(msg))

        except ParseError as e:
            pass

        return reply_obj

    @gen.coroutine
    def gen_orders(self):
        return self.orders.get_list_of_orders()
