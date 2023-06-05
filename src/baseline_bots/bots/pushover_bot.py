from typing import List

from daidepp import REJ, YES
from diplomacy import Game, Message
from tornado import gen

from baseline_bots.bots.dipnet_bot import DipnetBot
from baseline_bots.utils import (
    MessagesData,
    OrdersData,
    get_non_aggressive_orders,
    parse_arrangement,
    parse_daide,
)


class PushoverDipnet(DipnetBot):
    """
    Moves by Dipnet's orders and replace its own orders by the last proposal (if exists)
    NOTE: only executes non-aggressive action
    """

    orders: OrdersData

    def __init__(self, power_name: str, game: Game, total_msg_rounds=3) -> None:
        super().__init__(power_name, game, total_msg_rounds)

    @gen.coroutine
    def gen_messages(self, rcvd_messages: List[Message]) -> MessagesData:
        self.orders = OrdersData()
        reply_obj = MessagesData()

        orders = yield self.brain.get_orders(self.game, self.power_name)
        self.orders.add_orders(orders)

        if len(rcvd_messages) == 0:
            return reply_obj

        sorted_rcvd_messages = rcvd_messages
        last_message = sorted_rcvd_messages[0]
        while "FCT" in last_message.message:
            sorted_rcvd_messages.pop(0)
            if len(sorted_rcvd_messages) == 0:
                break
            last_message = sorted_rcvd_messages[0]

        if "FCT" in last_message.message or len(sorted_rcvd_messages) == 0:
            return reply_obj

        orders = get_non_aggressive_orders(
            parse_arrangement(last_message.message), self.power_name, self.game
        )
        # set the orders
        self.orders.add_orders(orders)

        # set message to say YES
        parsed_message = parse_daide(last_message.message)
        msg = YES(parsed_message)
        reply_obj.add_message(last_message.sender, str(msg))

        for message in sorted_rcvd_messages[1:]:
            if "FCT" not in message.message:
                parsed_message = parse_daide(message.message)
                msg = REJ(parsed_message)
                reply_obj.add_message(message.sender, str(msg))

        return reply_obj

    @gen.coroutine
    def __call__(self) -> List[str]:
        rcvd_messages = self.read_messages()
        messages = yield self.gen_messages(rcvd_messages)
        yield self.send_messages(messages)
        orders = list(self.orders)
        return orders
