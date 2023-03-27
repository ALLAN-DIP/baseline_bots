from typing import List, Optional

import DAIDE
from DAIDE import ParseError
from diplomacy import Game, Message
from tornado import gen

DAIDE.config.ORDERS_DAIDE = False

from baseline_bots.bots.baseline_bot import BaselineBot
from baseline_bots.utils import (
    REJ,
    YES,
    MessagesAndOrders,
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

    orders: Optional[OrdersData]

    def __init__(self, power_name: str, game: Game) -> None:
        super().__init__(power_name, game)
        self.orders = None

    def gen_messages(self, _) -> None:
        # Return data initialization
        return None

    def gen_orders(self) -> List[str]:
        return self.orders.get_list_of_orders()

    def __call__(self, rcvd_messages: List[Message]) -> MessagesAndOrders:
        ret_obj = OrdersData()
        reply_obj = MessagesData()

        if len(rcvd_messages) == 0:
            self.orders = ret_obj
            return {"orders": ret_obj, "messages": reply_obj}
        sorted_rcvd_messages = sort_messages_by_most_recent(rcvd_messages)
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
    def gen_messages(self, rcvd_messages: List[Message]) -> None:
        return super().gen_messages(rcvd_messages)

    @gen.coroutine
    def gen_orders(self) -> List[str]:
        return super().gen_orders()

    @gen.coroutine
    def __call__(self, rcvd_messages: List[Message]) -> MessagesAndOrders:
        return super().__call__(rcvd_messages)
