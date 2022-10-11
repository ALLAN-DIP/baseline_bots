__author__ = "Sander Schulhoff"
__email__ = "sanderschulhoff@gmail.com"

import DAIDE
from DAIDE import ALY, ORR, XDO, ParseError
from diplomacy import Message
from tornado import gen

DAIDE.config.ORDERS_DAIDE = False

from baseline_bots.bots.baseline_bot import BaselineBot
from baseline_bots.utils import (
    REJ,
    YES,
    MessagesData,
    OrdersData,
    get_non_aggressive_orders,
    parse_arrangement,
    sort_messages_by_most_recent,
)


class PushoverBot(BaselineBot):
    """
    Does whatever the last message/bot told it to do
    NOTE: only executes non-aggressive action
    """

    def __init__(self, power_name, game) -> None:
        super().__init__(power_name, game)
        self.orders = None

    def gen_messages(self, _):
        # Return data initialization
        return None

    def gen_orders(self):
        return self.orders.get_list_of_orders()

    def __call__(self, rcvd_messages):
        ret_obj = OrdersData()
        reply_obj = MessagesData()

        if len(rcvd_messages) == 0:
            self.orders = ret_obj
            return {"orders": ret_obj, "messages": reply_obj}
        # print(len(rcvd_messages))
        sorted_rcvd_messages = sort_messages_by_most_recent(rcvd_messages)
        # print(sorted_rcvd_messages)
        last_message = sorted_rcvd_messages[0]
        while "FCT" in last_message.message:
            sorted_rcvd_messages.pop(0)
            if len(sorted_rcvd_messages) == 0:
                break
            last_message = sorted_rcvd_messages[0]

        if "FCT" in last_message.message or len(sorted_rcvd_messages) == 0:
            self.orders = ret_obj
            return {"orders": ret_obj, "messages": reply_obj}

        # parse may fail
        try:
            # print(last_message.message)
            # print(parse_arrangement(last_message.message))
            orders = get_non_aggressive_orders(
                parse_arrangement(last_message.message), self.power_name, self.game
            )
            # set the orders
            ret_obj.add_orders(orders)

            # set message to say YES
            msg = YES(last_message.message)
            reply_obj.add_message(last_message.sender, str(msg))

            for message in sorted_rcvd_messages[1:]:
                if "FCT" not in last_message.message:
                    msg = REJ(message)
                    reply_obj.add_message(message.sender, str(msg))

        except ParseError as e:
            pass

        self.orders = ret_obj

        return {"orders": ret_obj, "messages": reply_obj}


class PushoverBot_AsyncBot(PushoverBot):
    """Wrapper to PushoverBot with tornado decorators for async calls"""

    @gen.coroutine
    def gen_messages(self, rcvd_messages):
        return super().gen_messages(rcvd_messages)

    @gen.coroutine
    def gen_orders(self):
        return super().gen_orders()

    @gen.coroutine
    def __call__(self, rcvd_messages):
        return super().__call__(rcvd_messages)
